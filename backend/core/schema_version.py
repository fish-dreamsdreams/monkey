"""内容 schema 版本。

职责：声明编辑器当前支持的项目结构版本，供创建项目与打开项目时对齐。
"""

CURRENT_SCHEMA_VERSION = "1.11.0"
SUPPORTED_SCHEMA_VERSIONS: frozenset[str] = frozenset(
    {
        "1.0.0",
        "1.1.0",
        "1.2.0",
        "1.3.0",
        "1.4.0",
        "1.5.0",
        "1.6.0",
        "1.7.0",
        "1.8.0",
        "1.9.0",
        "1.10.0",
        "1.11.0",
    }
)
API_VERSION = "0.12.0"
