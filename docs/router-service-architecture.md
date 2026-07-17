# Router service architecture

Backend giữ một ứng dụng FastAPI nhưng tách rõ ba lớp điều phối:

```text
API / Frontend
  -> RoutingService (facade)
     -> RuleBasedRouterService -> RuleV0Service / RuleV1Service / RuleV2Service / RuleV3Service
     -> SLMRouterService       -> QwenV0Service
     -> HybridV0Service (compatibility)
        -> adapter -> core router hoặc external Qwen service
```

`RoutingService` chỉ tìm service theo router ID và điều phối compare. Registry
của mỗi family phát hiện duplicate ID, kiểm tra router không tồn tại và cung
cấp metadata. Version service giữ application logic tối thiểu: chuẩn hóa input,
gọi adapter và trả `RouteResponse`.

Adapter chỉ tích hợp core router hoặc HTTP client. Các adapter V0, V1, V2 và
Qwen hiện hữu vẫn được giữ; V3 Phase 0 có adapter và core riêng được sao chép
cơ học từ V2 để làm baseline.

## Thêm router version

1. Tạo adapter implement `route` và giữ schema `RouteResponse`.
2. Tạo version service kế thừa `AdapterBackedRouterService`.
3. Đăng ký service trong registry family tương ứng.
4. Thêm router ID vào test và benchmark; không đổi ID cũ.

## Backward compatibility

Import cũ `app.services.routing_service.routing_service` vẫn trỏ tới facade
mới. Cả endpoint mới `/api/v1/router/*` và alias cũ `/api/v1/route`,
`/api/v1/compare`, `/api/v1/routers` đều được giữ.
