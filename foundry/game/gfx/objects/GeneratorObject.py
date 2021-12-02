from abc import ABC

from foundry.game.gfx.objects.ObjectLike import ObjectLike


class GeneratorObject(ObjectLike, ABC):
    domain: int
