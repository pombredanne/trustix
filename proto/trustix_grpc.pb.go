// Code generated by protoc-gen-go-grpc. DO NOT EDIT.

package proto

import (
	context "context"
	grpc "google.golang.org/grpc"
	codes "google.golang.org/grpc/codes"
	status "google.golang.org/grpc/status"
)

// This is a compile-time assertion to ensure that this generated file
// is compatible with the grpc package it is being compiled against.
const _ = grpc.SupportPackageIsVersion7

// TrustixCombinedRPCClient is the client API for TrustixCombinedRPC service.
//
// For semantics around ctx use and closing/ending streaming RPCs, please refer to https://pkg.go.dev/google.golang.org/grpc/?tab=doc#ClientConn.NewStream.
type TrustixCombinedRPCClient interface {
	// Get map[LogName]OutputHash
	Get(ctx context.Context, in *KeyRequest, opts ...grpc.CallOption) (*EntriesResponse, error)
	// Compare(inputHash)
	Decide(ctx context.Context, in *KeyRequest, opts ...grpc.CallOption) (*DecisionResponse, error)
}

type trustixCombinedRPCClient struct {
	cc grpc.ClientConnInterface
}

func NewTrustixCombinedRPCClient(cc grpc.ClientConnInterface) TrustixCombinedRPCClient {
	return &trustixCombinedRPCClient{cc}
}

func (c *trustixCombinedRPCClient) Get(ctx context.Context, in *KeyRequest, opts ...grpc.CallOption) (*EntriesResponse, error) {
	out := new(EntriesResponse)
	err := c.cc.Invoke(ctx, "/trustix.TrustixCombinedRPC/Get", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *trustixCombinedRPCClient) Decide(ctx context.Context, in *KeyRequest, opts ...grpc.CallOption) (*DecisionResponse, error) {
	out := new(DecisionResponse)
	err := c.cc.Invoke(ctx, "/trustix.TrustixCombinedRPC/Decide", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

// TrustixCombinedRPCServer is the server API for TrustixCombinedRPC service.
// All implementations must embed UnimplementedTrustixCombinedRPCServer
// for forward compatibility
type TrustixCombinedRPCServer interface {
	// Get map[LogName]OutputHash
	Get(context.Context, *KeyRequest) (*EntriesResponse, error)
	// Compare(inputHash)
	Decide(context.Context, *KeyRequest) (*DecisionResponse, error)
	mustEmbedUnimplementedTrustixCombinedRPCServer()
}

// UnimplementedTrustixCombinedRPCServer must be embedded to have forward compatible implementations.
type UnimplementedTrustixCombinedRPCServer struct {
}

func (UnimplementedTrustixCombinedRPCServer) Get(context.Context, *KeyRequest) (*EntriesResponse, error) {
	return nil, status.Errorf(codes.Unimplemented, "method Get not implemented")
}
func (UnimplementedTrustixCombinedRPCServer) Decide(context.Context, *KeyRequest) (*DecisionResponse, error) {
	return nil, status.Errorf(codes.Unimplemented, "method Decide not implemented")
}
func (UnimplementedTrustixCombinedRPCServer) mustEmbedUnimplementedTrustixCombinedRPCServer() {}

// UnsafeTrustixCombinedRPCServer may be embedded to opt out of forward compatibility for this service.
// Use of this interface is not recommended, as added methods to TrustixCombinedRPCServer will
// result in compilation errors.
type UnsafeTrustixCombinedRPCServer interface {
	mustEmbedUnimplementedTrustixCombinedRPCServer()
}

func RegisterTrustixCombinedRPCServer(s grpc.ServiceRegistrar, srv TrustixCombinedRPCServer) {
	s.RegisterService(&_TrustixCombinedRPC_serviceDesc, srv)
}

func _TrustixCombinedRPC_Get_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(KeyRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(TrustixCombinedRPCServer).Get(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/trustix.TrustixCombinedRPC/Get",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(TrustixCombinedRPCServer).Get(ctx, req.(*KeyRequest))
	}
	return interceptor(ctx, in, info, handler)
}

func _TrustixCombinedRPC_Decide_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(KeyRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(TrustixCombinedRPCServer).Decide(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/trustix.TrustixCombinedRPC/Decide",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(TrustixCombinedRPCServer).Decide(ctx, req.(*KeyRequest))
	}
	return interceptor(ctx, in, info, handler)
}

var _TrustixCombinedRPC_serviceDesc = grpc.ServiceDesc{
	ServiceName: "trustix.TrustixCombinedRPC",
	HandlerType: (*TrustixCombinedRPCServer)(nil),
	Methods: []grpc.MethodDesc{
		{
			MethodName: "Get",
			Handler:    _TrustixCombinedRPC_Get_Handler,
		},
		{
			MethodName: "Decide",
			Handler:    _TrustixCombinedRPC_Decide_Handler,
		},
	},
	Streams:  []grpc.StreamDesc{},
	Metadata: "trustix.proto",
}
