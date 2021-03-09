from trustix_proto import trustix_pb2_grpc  # type: ignore
from trustix_api import api_pb2
from fastapi.staticfiles import StaticFiles
from fastapi.templating import (
    Jinja2Templates,
)
from fastapi.responses import (
    HTMLResponse,
)
from fastapi import (
    FastAPI,
    Request,
    Form,
)
from typing import (
    Optional,
    Dict,
    List,
    Set,
)
from trustix_dash import template_lib
from trustix_dash.models import (
    DerivationOutputResult,
    DerivationOutput,
    DerivationAttr,
    Derivation,
    Log,
)
from tortoise import Tortoise
import urllib.parse
import Levenshtein
import requests
import tempfile
import asyncio
import os.path
import codecs
import shlex
import json
import grpc  # type: ignore

from trustix_dash.api import (
    get_derivation_output_results,
    get_derivation_outputs,
    evaluation_list,
)

BINARY_CACHE_PROXY = "http://localhost:8080"
DEFAULT_ATTR = "hello.x86_64-linux"

TRUSTIX_RPC = "unix:../../sock"
channel = grpc.aio.insecure_channel(TRUSTIX_RPC)
stub = trustix_pb2_grpc.TrustixCombinedRPCStub(channel)


SCRIPT_DIR = os.path.dirname(__file__)

templates = Jinja2Templates(directory=os.path.join(SCRIPT_DIR, "templates"))
templates.env.globals["drv_url_quote"] = template_lib.drv_url_quote
templates.env.globals["json_render"] = template_lib.json_render


app = FastAPI()
app.mount(
    "/static", StaticFiles(directory=os.path.join(SCRIPT_DIR, "static")), name="static"
)


@app.on_event("startup")
async def startup_event():
    await Tortoise.init(
        {
            "connections": {
                "default": "sqlite://db.sqlite3",
            },
            "apps": {
                "trustix_dash": {
                    "models": ["trustix_dash.models"],
                }
            },
            "use_tz": False,
            "timezone": "UTC",
        }
    )


@app.on_event("shutdown")
async def close_orm():
    await Tortoise.close_connections()


async def make_context(
    request: Request,
    title: str = "",
    selected_evaluation: Optional[str] = None,
    extra: Optional[Dict] = None,
) -> Dict:

    evaluations = await evaluation_list()
    if selected_evaluation and selected_evaluation not in evaluations:
        evaluations.insert(0, selected_evaluation)

    if not selected_evaluation:
        try:
            selected_evaluation = evaluations[0]
        except IndexError:
            pass

    ctx = {
        "evaluations": evaluations,
        "selected_evaluation": selected_evaluation,
        "request": request,
        "title": "Trustix R13Y" + (" ".join((" - ", title)) if title else ""),
        "drv_placeholder": DEFAULT_ATTR,
    }

    if extra:
        ctx.update(extra)

    return ctx


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    ctx = await make_context(
        request,
        extra={
            "attr": DEFAULT_ATTR,
        },
    )
    return templates.TemplateResponse("index.jinja2", ctx)


@app.get("/drv/{drv_path}", response_class=HTMLResponse)
async def drv(request: Request, drv_path: str):

    drv_path = urllib.parse.unquote(drv_path)
    drvs = await get_derivation_outputs(drv_path)

    # Description: drv -> output -> output_hash -> List[result]
    PATH_T = Dict[str, Dict[str, Dict[str, List[DerivationOutputResult]]]]
    unreproduced_paths: PATH_T = {}
    reproduced_paths: PATH_T = {}
    # Paths only built by one log
    unknown_paths: PATH_T = {}
    # Paths not built by any known log
    missing_paths: PATH_T = {}

    log_ids: Set[int] = set()

    def append_output(paths_d: PATH_T, drv: Derivation, output: DerivationOutput):
        """Append an output to the correct datastructure (paths_d)"""
        current = paths_d.setdefault(drv.drv, {}).setdefault(output.output, {})
        for result in output.derivationoutputresults:  # type: ignore
            current.setdefault(
                codecs.encode(result.output_hash, "hex").decode(), []
            ).append(result)
            log_ids.add(result.log_id)

    num_outputs: int = 0

    for drv in drvs:
        output: DerivationOutput
        for output in drv.derivationoutputs:  # type: ignore
            output_hashes: Set[bytes] = set(
                result.output_hash for result in output.derivationoutputresults  # type: ignore
            )

            num_outputs += 1

            if not output_hashes:
                append_output(missing_paths, drv, output)

            elif len(output_hashes) == 1 and len(output.derivationoutputresults) > 1:  # type: ignore
                append_output(reproduced_paths, drv, output)

            elif len(output_hashes) == 1:
                append_output(unknown_paths, drv, output)

            elif len(output_hashes) > 1:
                append_output(unreproduced_paths, drv, output)

            else:
                raise RuntimeError("Logic error")

    logs: Dict[int, Log] = {
        log.id: log for log in await Log.filter(id__in=log_ids)  # type: ignore
    }

    num_reproduced = sum(len(v) for v in reproduced_paths.values())

    ctx = await make_context(
        request,
        extra={
            "unreproduced_paths": unreproduced_paths,
            "reproduced_paths": reproduced_paths,
            "unknown_paths": unknown_paths,
            "missing_paths": missing_paths,
            "drv_path": drv_path,
            "logs": logs,
            "statistics": {
                "pct_reproduced": round(num_outputs / 100 * num_reproduced, 2),
                "num_reproduced": num_reproduced,
                "num_outputs": num_outputs,
            },
        },
    )

    return templates.TemplateResponse("drv.jinja2", ctx)


@app.post("/search/")
async def search(request: Request, term: str = Form(...)):
    from trustix_dash.models import DerivationAttr

    if len(term) < 3:
        raise ValueError("Search term too short")

    qs = DerivationAttr.filter(attr__startswith=term)

    results = await qs

    derivations_by_attr: Dict[str, Set[str]] = {}
    for result in results:
        derivations_by_attr.setdefault(result.attr, set()).add(result.derivation_id)

    ctx = await make_context(
        request,
        extra={
            "derivations_by_attr": derivations_by_attr,
        },
    )

    return templates.TemplateResponse("search.jinja2", ctx)


@app.get("/suggest/{attr}", response_model=List[str])
async def suggest(request: Request, attr: str):
    if len(attr) < 3:
        raise ValueError("Prefix too short")

    resp = await DerivationAttr.filter(attr__startswith=attr).only("attr")
    return sorted(
        (drv_attr.attr for drv_attr in resp),
        key=lambda x: Levenshtein.ratio(attr, x),
        reverse=True,
    )


@app.post("/diff/", response_class=HTMLResponse)
async def diff(request: Request, output_hash: List[str] = Form(...)):

    if len(output_hash) < 1:
        raise ValueError("Need at least 2 entries to diff")
    if len(output_hash) > 2:
        raise ValueError("Received more than 2 entries to diff")

    output_hash_1, output_hash_2 = [codecs.decode(h, "hex") for h in output_hash]

    result1, result2 = await get_derivation_output_results(output_hash_1, output_hash_2)

    # Uvloop has a nasty bug https://github.com/MagicStack/uvloop/issues/317
    # To work around this we run the fetching/unpacking in a separate blocking thread
    def fetch_unpack_nar(url, location):
        import subprocess

        loc_base = os.path.basename(location)
        loc_dir = os.path.dirname(location)

        try:
            os.mkdir(loc_dir)
        except FileExistsError:
            pass

        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            p = subprocess.Popen(
                ["nix-nar-unpack", loc_base], stdin=subprocess.PIPE, cwd=loc_dir
            )
            for chunk in r.iter_content(chunk_size=512):
                p.stdin.write(chunk)
            p.stdin.close()
            p.wait(timeout=0.5)

        # Ensure correct mtime
        for subl in (
            (os.path.join(dirpath, f) for f in (dirnames + filenames))
            for (dirpath, dirnames, filenames) in os.walk(location)
        ):
            for path in subl:
                os.utime(path, (1, 1))
        os.utime(location, (1, 1))

    async def process_result(result, tmpdir, outbase) -> str:
        # Fetch narinfo
        narinfo = json.loads(
            (await stub.GetValue(api_pb2.ValueRequest(Digest=result.output_hash))).Value
        )
        nar_hash = narinfo["narHash"].split(":")[-1]

        # Get store prefix
        output = await result.output

        store_base = output.store_path.split("/")[-1]
        store_prefix = store_base.split("-")[0]

        unpack_dir = os.path.join(tmpdir, store_base, outbase)
        nar_url = "/".join((BINARY_CACHE_PROXY, "nar", store_prefix, nar_hash))

        await asyncio.get_running_loop().run_in_executor(
            None, fetch_unpack_nar, nar_url, unpack_dir
        )

        return unpack_dir

    # TODO: Async tempfile
    with tempfile.TemporaryDirectory(prefix="trustix-ui-dash-diff") as tmpdir:
        dir_a, dir_b = await asyncio.gather(
            process_result(result1, tmpdir, "A"),
            process_result(result2, tmpdir, "B"),
        )

        dir_a_rel = os.path.join(os.path.basename(os.path.dirname(dir_a)), "A")
        dir_b_rel = os.path.join(os.path.basename(os.path.dirname(dir_b)), "B")

        proc = await asyncio.create_subprocess_shell(
            shlex.join(["diffoscope", "--html", "-", dir_a_rel, dir_b_rel]),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=tmpdir,
        )
        stdout, stderr = await proc.communicate()

    # Diffoscope returns non-zero on paths that have a diff
    # Instead use stderr as a heurestic if the call went well or not
    if stderr:
        raise ValueError(stderr)

    return stdout