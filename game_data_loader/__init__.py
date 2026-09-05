"""游戏客户端示例加载器。

只读 packages/game-data-schema 冻结合同与导出目录，不连接编辑器数据库，不结算战斗。
"""

from game_data_loader.errors import ClientChecksumError, ClientPackageError, ClientSchemaError
from game_data_loader.loader import load_export_dir
from game_data_loader.models import GameData, RuntimeCharacter, RuntimeCity, RuntimeFaction, RuntimeSkill

__all__ = [
    "ClientChecksumError",
    "ClientPackageError",
    "ClientSchemaError",
    "GameData",
    "RuntimeCharacter",
    "RuntimeCity",
    "RuntimeFaction",
    "RuntimeSkill",
    "load_export_dir",
]
