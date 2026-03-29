# Proto generation: outputs to gen/proto/ (module=lunar-tear/server).
# All proto files have go_package. Only protos used by the server are generated here
# (generating all would put them in one package and cause name clashes).
PROTO_USED = proto/banner.proto proto/battle.proto proto/cageornament.proto proto/characterviewer.proto proto/config.proto proto/costume.proto proto/data.proto proto/deck.proto proto/dokan.proto proto/friend.proto proto/gacha.proto proto/gameplay.proto proto/gift.proto proto/gimmick.proto proto/loginbonus.proto proto/mission.proto proto/movie.proto proto/navicutin.proto proto/omikuji.proto proto/notification.proto proto/portalcage.proto proto/quest.proto proto/shop.proto proto/tutorial.proto proto/user.proto

proto:
	protoc -I . $(PROTO_USED) --go_out=. --go_opt=module=lunar-tear/server --go-grpc_out=. --go-grpc_opt=module=lunar-tear/server
	@echo "Generated in gen/proto/"

.PHONY: proto
