"""客户端加载错误。独立于编辑器 AppError。"""


class ClientPackageError(Exception):
    """导出包无法被游戏客户端加载。"""


class ClientSchemaError(ClientPackageError):
    """schema_version 与冻结合同不一致。"""


class ClientChecksumError(ClientPackageError):
    """分区 checksum 不匹配。"""
