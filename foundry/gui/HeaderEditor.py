from attr import attrs, evolve
from PySide6.QtCore import Signal, SignalInstance
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QLabel, QTabWidget, QVBoxLayout, QWidget

from foundry.core.UndoController import UndoController
from foundry.game.level.Level import Level
from foundry.game.level.util import Level as LevelInformationState
from foundry.game.level.util import find_level_by_pointers
from foundry.gui.CustomDialog import CustomDialog
from foundry.gui.LevelDataEditor import LevelDataEditor, LevelDataState
from foundry.gui.LevelGraphicsEditor import LevelGraphicsEditor, LevelGraphicsState
from foundry.gui.LevelInformationEditor import LevelInformationEditor
from foundry.gui.LevelStartEditor import LevelStartEditor, LevelStartState
from foundry.gui.LevelWarpEditor import LevelWarpEditor, LevelWarpState
from foundry.gui.settings import FileSettings
from foundry.smb3parse.constants import TILESET_LEVEL_OFFSET
from foundry.smb3parse.levels import ENEMY_BASE_OFFSET, LEVEL_BASE_OFFSET


@attrs(slots=True, auto_attribs=True, eq=True, frozen=True, hash=True)
class HeaderState:
    """
    The representation of a the level header.

    Attributes
    ----------
    data: LevelDataState
        The miscellaneous level data.
    start: LevelStartState
        The starting conditions of the level.
    graphics: LevelGraphicsState
        The graphics of the level.
    warp: LevelWarpState
        The next level to be warped to.
    info: LevelInformationState
        The editor specific information associated with the level.
    """

    data: LevelDataState
    start: LevelStartState
    graphics: LevelGraphicsState
    warp: LevelWarpState
    info: LevelInformationState


def level_to_header_state(level: Level, file_settings: FileSettings) -> HeaderState:
    """
    Generates a header state from a level.

    Parameters
    ----------
    level : Level
        To generate the header state from.
    file_settings: FileSettings
        To generate the level information from.

    Returns
    -------
    HeaderState
        The header state that corresponds to the level.
    """
    return HeaderState(
        LevelDataState(
            level.length // 0x10,
            level.music_index,
            level.time_index,
            level.scroll_type,
            not level.is_vertical,
            level.pipe_ends_level,
        ),
        LevelStartState(level.start_x_index, level.start_y_index, level.start_action),
        LevelGraphicsState(level.object_palette_index, level.enemy_palette_index, level.graphic_set),
        LevelWarpState(level.next_area_objects, level.next_area_enemies, level.next_area_object_set),
        find_level_by_pointers(file_settings.levels, level.object_offset, level.enemy_offset)
        or file_settings.levels[0],
    )


def header_state_to_level_header(state: HeaderState) -> bytearray:
    """
    Generates a 9-byte header for a level for SMB3 from a header state.

    Parameters
    ----------
    state : HeaderState
        To be converted to a level header.

    Returns
    -------
    bytearray
        A series of nine bytes that represent a level header inside SMB3.

    Notes
    -----
    The format of the level header is as follows

    Byte 0x02-1:
        The next level's generator pointer.
    Byte 0x04-3:
        The next level's enemy pointer.
    Byte 0x05:
        The level length in increments of 16 followed by the y start of the player.
    Byte 0x06:
        The generator's palette, enemy's palette followed by the x start of the player.
    Byte 0x07:
        The tileset of the level, if the level is vertical, the type of scroll used by the level,
        followed by if the level ends when the player enters a pipe.
    Byte 0x08:
        The graphics set of the level followed by the starting action of the player.
    Byte 0x09:
        The music of the level followed by the time provided to the player.
    """
    data = bytearray()

    generator_pointer = state.warp.generator_pointer - LEVEL_BASE_OFFSET - TILESET_LEVEL_OFFSET[state.warp.tileset]
    enemy_pointer = state.warp.enemy_pointer - ENEMY_BASE_OFFSET

    data.append(0x00FF & generator_pointer)
    data.append((0xFF00 & generator_pointer) >> 8)
    data.append(0x00FF & enemy_pointer)
    data.append((0xFF00 & enemy_pointer) >> 8)
    data.append((state.start.y_position << 5) + state.data.level_length)
    data.append(state.graphics.generator_palette + (state.graphics.enemy_palette << 3) + (state.start.x_position << 5))
    data.append(
        state.warp.tileset
        + (int(not state.data.horizontal) << 4)
        + (state.data.scroll << 5)
        + (int(state.data.pipe_ends_level) << 7)
    )
    data.append(state.graphics.graphics_set + (state.start.action << 5))
    data.append(state.data.music + (state.data.time << 6))

    return data


class HeaderEditor(CustomDialog):
    """
    A widget which controls the editing of the level header.

    Signals
    -------
    level_length_changed: SignalInstance
        A signal which is activated on level length change.
    music_changed: SignalInstance
        A signal which is activated on music change.
    time_changed: SignalInstance
        A signal which is activated on time change.
    scroll_changed: SignalInstance
        A signal which is activated on scroll type change.
    horizontal_changed: SignalInstance
        A signal which is activated on level horizontality change.
    pipe_ends_level_changed: SignalInstance
        A signal which is activated on if pipe ends level change.
    x_position_changed: SignalInstance
        A signal which is activated on x position change.
    y_position_changed: SignalInstance
        A signal which is activated on y position change.
    action_changed: SignalInstance
        A signal which is activated on action change.
    generator_palette_changed: SignalInstance
        A signal which is activated on generator palette change.
    enemy_palette_changed: SignalInstance
        A signal which is activated on enemy palette change.
    graphics_set_changed: SignalInstance
        A signal which is activated on graphics set change.
    next_level_generator_pointer_changed: SignalInstance
        A signal which is activated on next level generator pointer change.
    next_level_enemy_pointer_changed: SignalInstance
        A signal which is activated on next level enemy pointer change.
    next_level_tileset_changed: SignalInstance
        A signal which is activated on next level tileset change.
    name_changed: SignalInstance
        A signal which is activated on name change.
    description_changed: SignalInstance
        A signal which is activated on description change.
    generator_space_changed: SignalInstance
        A signal which is activated on generation space change.
    enemy_space_changed: SignalInstance
        A signal which is activated on enemy space change.
    state_changed: SignalInstance
        A signal which is activated on any state change.

    Attributes
    ----------
    undo_controller: UndoController[HeaderState]
        The undo controller, which is responsible for undoing and redoing any action.
    file_settings: FileSettings
        The settings for determining levels to automatically select the warp state from.

    """

    level_length_changed: SignalInstance = Signal(int)  # type: ignore
    music_changed: SignalInstance = Signal(int)  # type: ignore
    time_changed: SignalInstance = Signal(int)  # type: ignore
    scroll_changed: SignalInstance = Signal(int)  # type: ignore
    horizontal_changed: SignalInstance = Signal(bool)  # type: ignore
    pipe_ends_level_changed: SignalInstance = Signal(bool)  # type: ignore
    x_position_changed: SignalInstance = Signal(int)  # type: ignore
    y_position_changed: SignalInstance = Signal(int)  # type: ignore
    action_changed: SignalInstance = Signal(int)  # type: ignore
    generator_palette_changed: SignalInstance = Signal(int)  # type: ignore
    enemy_palette_changed: SignalInstance = Signal(int)  # type: ignore
    graphics_set_changed: SignalInstance = Signal(int)  # type: ignore
    next_level_generator_pointer_changed: SignalInstance = Signal(int)  # type: ignore
    next_level_enemy_pointer_changed: SignalInstance = Signal(int)  # type: ignore
    next_level_tileset_changed: SignalInstance = Signal(int)  # type: ignore
    name_changed: SignalInstance = Signal(str)  # type: ignore
    description_changed: SignalInstance = Signal(str)  # type: ignore
    generator_space_changed: SignalInstance = Signal(int)  # type: ignore
    enemy_space_changed: SignalInstance = Signal(int)  # type: ignore

    state_changed: SignalInstance = Signal(object)  # type: ignore

    undo_controller: UndoController[HeaderState]

    def __init__(
        self,
        parent: QWidget | None,
        state: HeaderState,
        file_settings: FileSettings,
        undo_controller: UndoController[HeaderState] | None = None,
    ):
        super().__init__(parent, "Level Header Editor")
        self.file_settings = file_settings
        self._state = state
        self.undo_controller = undo_controller or UndoController(state)

        self._display = HeaderDisplay(
            self,
            self.state.data,
            self.state.start,
            self.state.graphics,
            self.state.warp,
            self.state.info,
            header_state_to_level_header(self.state),
            self.file_settings,
        )

        self.setLayout(self._display)

        # Connect signals accordingly
        self._display.data_editor.level_length_changed.connect(self._level_length_changed)
        self._display.data_editor.music_changed.connect(self._music_changed)
        self._display.data_editor.time_changed.connect(self._time_changed)
        self._display.data_editor.scroll_changed.connect(self._scroll_changed)
        self._display.data_editor.horizontal_changed.connect(self._horizontal_changed)
        self._display.data_editor.pipe_ends_level_changed.connect(self._pipe_ends_level_changed)
        self._display.start_editor.x_position_changed.connect(self._x_position_changed)
        self._display.start_editor.y_position_changed.connect(self._y_position_changed)
        self._display.start_editor.action_changed.connect(self._action_changed)
        self._display.graphics_editor.generator_palette_changed.connect(self._generator_palette_changed)
        self._display.graphics_editor.enemy_palette_changed.connect(self._enemy_palette_changed)
        self._display.graphics_editor.graphics_set_changed.connect(self._graphics_set_changed)
        self._display.warp_editor.generator_pointer_changed.connect(self._next_level_generator_pointer_changed)
        self._display.warp_editor.enemy_pointer_changed.connect(self._next_level_enemy_pointer_changed)
        self._display.warp_editor.tileset_changed.connect(self._next_level_tileset_changed)
        self._display.info_editor.name_changed.connect(self._name_changed)
        self._display.info_editor.description_changed.connect(self._description_changed)
        self._display.info_editor.generator_space_changed.connect(self._generator_space_changed)
        self._display.info_editor.enemy_space_changed.connect(self._enemy_space_changed)

        self._display.data_editor.level_length_changed.connect(self.level_length_changed)
        self._display.data_editor.music_changed.connect(self.music_changed)
        self._display.data_editor.time_changed.connect(self.time_changed)
        self._display.data_editor.scroll_changed.connect(self.scroll_changed)
        self._display.data_editor.horizontal_changed.connect(self.horizontal_changed)
        self._display.data_editor.pipe_ends_level_changed.connect(self.pipe_ends_level_changed)
        self._display.start_editor.x_position_changed.connect(self.x_position_changed)
        self._display.start_editor.y_position_changed.connect(self.y_position_changed)
        self._display.start_editor.action_changed.connect(self.action_changed)
        self._display.graphics_editor.generator_palette_changed.connect(self.generator_palette_changed)
        self._display.graphics_editor.enemy_palette_changed.connect(self.enemy_palette_changed)
        self._display.graphics_editor.graphics_set_changed.connect(self.graphics_set_changed)
        self._display.warp_editor.generator_pointer_changed.connect(self.next_level_generator_pointer_changed)
        self._display.warp_editor.enemy_pointer_changed.connect(self.next_level_enemy_pointer_changed)
        self._display.warp_editor.tileset_changed.connect(self.next_level_tileset_changed)
        self._display.info_editor.name_changed.connect(self.name_changed)
        self._display.info_editor.description_changed.connect(self.description_changed)
        self._display.info_editor.generator_space_changed.connect(self.generator_space_changed)
        self._display.info_editor.enemy_space_changed.connect(self.enemy_space_changed)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.parent}, {self.state}, {self.file_settings}, {self.undo_controller})"

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, HeaderEditor)
            and self.state == other.state
            and self.undo_controller == other.undo_controller
        )

    @property
    def current_page(self) -> int:
        """
        The current page accessed by the user.

        Returns
        -------
        int
            The index of the current page accessed.

        """
        return self._display.current_page

    @current_page.setter
    def current_page(self, page: int):
        self._display.current_page = page

    @property
    def level_length(self) -> int:
        """
        Provides the length of the level.

        Returns
        -------
        int
            The length of the level.

        """
        return self.state.data.level_length

    @level_length.setter
    def level_length(self, level_length: int):
        if self.level_length != level_length:
            self.do(evolve(self.state, data=evolve(self.state.data, level_length=level_length)))
            self.level_length_changed.emit(level_length)

    @property
    def music(self) -> int:
        """
        Provides the music of the level.

        Returns
        -------
        int
            The music of the level.

        """
        return self.state.data.music

    @music.setter
    def music(self, music: int):
        if self.music != music:
            self.do(evolve(self.state, data=evolve(self.state.data, music=music)))
            self.music_changed.emit(music)

    @property
    def time(self) -> int:
        """
        Provides the time of the level.

        Returns
        -------
        int
            The time of the level.
        """
        return self.state.data.time

    @time.setter
    def time(self, time: int):
        if self.time != time:
            self.do(evolve(self.state, data=evolve(self.state.data, time=time)))
            self.time_changed.emit(time)

    @property
    def scroll(self) -> int:
        """
        Provides the scroll of the level.

        Returns
        -------
        int
            The scroll of the level.
        """
        return self.state.data.scroll

    @scroll.setter
    def scroll(self, scroll: int):
        if self.scroll != scroll:
            self.do(evolve(self.state, data=evolve(self.state.data, scroll=scroll)))
            self.scroll_changed.emit(scroll)

    @property
    def horizontal(self) -> bool:
        """
        Provides if the level is horizontal.

        Returns
        -------
        bool
            If the level is horizontal.
        """
        return self.state.data.horizontal

    @horizontal.setter
    def horizontal(self, horizontal: bool):
        if self.horizontal != horizontal:
            self.do(evolve(self.state, data=evolve(self.state.data, horizontal=horizontal)))
            self.horizontal_changed.emit(horizontal)

    @property
    def pipe_ends_level(self) -> bool:
        """
        Provides if entering a pipe will end the level.

        Returns
        -------
        bool
            If the entering pipes end the level.
        """
        return self.state.data.pipe_ends_level

    @pipe_ends_level.setter
    def pipe_ends_level(self, pipe_ends_level: bool):
        if self.pipe_ends_level != pipe_ends_level:
            self.do(evolve(self.state, data=evolve(self.state.data, pipe_ends_level=pipe_ends_level)))
            self.pipe_ends_level_changed.emit(pipe_ends_level)

    @property
    def x_position(self) -> int:
        """
        Provides the x position the player starts at.

        Returns
        -------
        int
            The x position for the player starts at.
        """
        return self.state.start.x_position

    @x_position.setter
    def x_position(self, x_position: int):
        if self.x_position != x_position:
            self.do(evolve(self.state, start=evolve(self.state.start, x_position=x_position)))
            self.x_position_changed.emit(x_position)

    @property
    def y_position(self) -> int:
        """
        Provides the y position the player starts at.

        Returns
        -------
        int
            The y position the player starts at.
        """
        return self.state.start.y_position

    @y_position.setter
    def y_position(self, y_position: int):
        if self.y_position != y_position:
            self.do(evolve(self.state, start=evolve(self.state.start, y_position=y_position)))
            self.y_position_changed.emit(y_position)

    @property
    def action(self) -> int:
        """
        Provides the action the player starts at.

        Returns
        -------
        int
            The action the player starts at.
        """
        return self.state.start.action

    @action.setter
    def action(self, action: int):
        if self.action != action:
            self.do(evolve(self.state, start=evolve(self.state.start, action=action)))
            self.action_changed.emit(action)

    @property
    def generator_palette(self) -> int:
        """
        Provides the generator palette of this level.

        Returns
        -------
        int
            The generator palette of for this level.
        """
        return self.state.graphics.generator_palette

    @generator_palette.setter
    def generator_palette(self, generator_palette: int):
        if self.generator_palette != generator_palette:
            self.do(evolve(self.state, graphics=evolve(self.state.graphics, generator_palette=generator_palette)))
            self.generator_palette_changed.emit(generator_palette)

    @property
    def enemy_palette(self) -> int:
        """
        Provides the enemy palette of this level.

        Returns
        -------
        int
            The enemy palette of for this level.
        """
        return self.state.graphics.enemy_palette

    @enemy_palette.setter
    def enemy_palette(self, enemy_palette: int):
        if self.enemy_palette != enemy_palette:
            self.do(evolve(self.state, graphics=evolve(self.state.graphics, enemy_palette=enemy_palette)))
            self.enemy_palette_changed.emit(enemy_palette)

    @property
    def graphics_set(self) -> int:
        """
        Provides the graphics set of this level.

        Returns
        -------
        int
            The graphics set of for this level.
        """
        return self.state.graphics.graphics_set

    @graphics_set.setter
    def graphics_set(self, graphics_set: int):
        if self.graphics_set != graphics_set:
            self.do(evolve(self.state, graphics=evolve(self.state.graphics, graphics_set=graphics_set)))
            self.graphics_set_changed.emit(graphics_set)

    @property
    def next_level_generator_pointer(self) -> int:
        """
        Provides the generator pointer of the level that it will be warped to.

        Returns
        -------
        int
            The generator pointer of the next level.
        """
        return self.state.warp.generator_pointer

    @next_level_generator_pointer.setter
    def next_level_generator_pointer(self, generator_pointer: int):
        if self.next_level_generator_pointer != generator_pointer:
            self.do(evolve(self.state, warp=evolve(self.state.warp, generator_pointer=generator_pointer)))
            self.next_level_generator_pointer_changed.emit(generator_pointer)

    @property
    def next_level_enemy_pointer(self) -> int:
        """
        Provides the enemy pointer of the level that it will be warped to.

        Returns
        -------
        int
            The enemy pointer of the next level.
        """
        return self.state.warp.enemy_pointer

    @next_level_enemy_pointer.setter
    def next_level_enemy_pointer(self, enemy_pointer: int):
        print(enemy_pointer, type(enemy_pointer))
        if self.next_level_enemy_pointer != enemy_pointer:
            self.do(evolve(self.state, warp=evolve(self.state.warp, enemy_pointer=enemy_pointer)))
            self.next_level_enemy_pointer_changed.emit(enemy_pointer)

    @property
    def next_level_tileset(self) -> int:
        """
        Provides the tileset of the level that it will be warped to.

        Returns
        -------
        int
            The tileset of the next level.
        """
        return self.state.warp.tileset

    @next_level_tileset.setter
    def next_level_tileset(self, tileset: int):
        if self.next_level_tileset != tileset:
            self.do(evolve(self.state, warp=evolve(self.state.warp, tileset=tileset)))
            self.next_level_tileset_changed.emit(tileset)

    @property
    def name(self) -> str:
        """
        Provides the name of the level.

        Returns
        -------
        str
            The name of the level.
        """
        return self.state.info.display_information.name or ""

    @name.setter
    def name(self, name: str):
        if self.name != name:
            self.do(
                evolve(
                    self.state,
                    info=evolve(
                        self.state.info, display_information=evolve(self.state.info.display_information, name=name)
                    ),
                )
            )
            self.name_changed.emit(name)

    @property
    def description(self) -> str:
        """
        Provides the description of the level.

        Returns
        -------
        str
            The description of the level.
        """
        return self.state.info.display_information.description or ""

    @description.setter
    def description(self, description: str):
        if self.description != description:
            self.do(
                evolve(
                    self.state,
                    info=evolve(
                        self.state.info,
                        display_information=evolve(self.state.info.display_information, description=description),
                    ),
                )
            )
            self.description_changed.emit(description)

    @property
    def generator_space(self) -> int:
        """
        Provides the space for generators inside of the level.

        Returns
        -------
        int
            The space for generators inside of the level.
        """
        return self.state.info.generator_size

    @generator_space.setter
    def generator_space(self, generator_space: int):
        if self.generator_space != generator_space:
            self.do(evolve(self.state, info=evolve(self.state.info, generator_size=generator_space)))
            self.generator_space_changed.emit(generator_space)

    @property
    def enemy_space(self) -> int:
        """
        Provides the space for enemies inside of the level.

        Returns
        -------
        int
            The space for enemies inside of the level.
        """
        return self.state.info.enemy_size

    @enemy_space.setter
    def enemy_space(self, enemy_space: int):
        if self.enemy_space != enemy_space:
            self.do(evolve(self.state, info=evolve(self.state.info, enemy_size=enemy_space)))
            self.enemy_space_changed.emit(enemy_space)

    @property
    def state(self) -> HeaderState:
        return self._state

    @state.setter
    def state(self, state: HeaderState):
        if self.state != state:
            self.do(state)

    def do(self, new_state: HeaderState) -> HeaderState:
        """
        Does an action through the controller, adding it to the undo stack and clearing the redo
        stack, respectively.

        Parameters
        ----------
        new_state : HeaderState
            The new state to be stored.

        Returns
        -------
        HeaderState
            The new state that has been stored.
        """
        self._update_state(new_state)
        return self.undo_controller.do(new_state)

    @property
    def can_undo(self) -> bool:
        """
        Determines if there is any states inside the undo stack.

        Returns
        -------
        bool
            If there is an undo state available.
        """
        return self.undo_controller.can_undo

    def undo(self) -> HeaderState:
        """
        Undoes the last state, bring the previous.

        Returns
        -------
        HeaderState
            The new state that has been stored.
        """
        self._update_state(self.undo_controller.undo())
        return self.state

    @property
    def can_redo(self) -> bool:
        """
        Determines if there is any states inside the redo stack.

        Returns
        -------
        bool
            If there is an redo state available.
        """
        return self.undo_controller.can_redo

    def redo(self) -> HeaderState:
        """
        Redoes the previously undone state.

        Returns
        -------
        HeaderState
            The new state that has been stored.
        """
        self._update_state(self.undo_controller.redo())
        return self.state

    def _update_state(self, state: HeaderState):
        """
        Handles all updating of the state, sending any signals and updates to the display if needed.

        Parameters
        ----------
        state : HeaderState
            The new state of the editor.
        """

        self._state = state

        # Let the display do the heavy lifting for generating the updates.
        self._display.data = state.data
        self._display.start = state.start
        self._display.graphics = state.graphics
        self._display.warp = state.warp
        self._display.info = state.info

        # Update the level header's bytes
        self.level_bytes = header_state_to_level_header(state)

        self.state_changed.emit(state)

    def _level_length_changed(self, value: int):
        self.level_length = value

    def _music_changed(self, value: int):
        self.music = value

    def _time_changed(self, value: int):
        self.time = value

    def _scroll_changed(self, value: int):
        self.scroll = value

    def _horizontal_changed(self, value: bool):
        self.horizontal = value

    def _pipe_ends_level_changed(self, value: bool):
        self.pipe_ends_level = value

    def _x_position_changed(self, value: int):
        self.x_position = value

    def _y_position_changed(self, value: int):
        self.y_position = value

    def _action_changed(self, value: int):
        self.action = value

    def _generator_palette_changed(self, value: int):
        self.generator_palette = value

    def _enemy_palette_changed(self, value: int):
        self.enemy_palette = value

    def _next_level_generator_pointer_changed(self, value: int):
        self.next_level_generator_pointer = value

    def _next_level_enemy_pointer_changed(self, value: int):
        assert isinstance(value, int)
        print(value)
        self.next_level_enemy_pointer = value

    def _next_level_tileset_changed(self, value: int):
        self.next_level_tileset = value

    def _name_changed(self, value: str):
        self.name = value

    def _description_changed(self, value: str):
        self.description = value

    def _generator_space_changed(self, value: int):
        self.generator_space = value

    def _enemy_space_changed(self, value: int):
        self.enemy_space = value

    def _graphics_set_changed(self, value: int):
        self.graphics_set = value


class HeaderDisplay(QVBoxLayout):
    """
    The active display for all of the level's attributes defined inside the level header.

    Attributes
    ----------
    data_editor: LevelDataEditor
        The editor for this level's miscellaneous attributes.
    start_editor: LevelStartEditor
        The editor for this level's start placement and action.
    graphics_editor: LevelGraphicsEditor
        The editor for this level's graphics.
    warp_editor: LevelWarpEditor
        The editor for selecting the next level.
    info_editor: LevelInformationEditor
        The editor for adjusting this level's information.
    """

    data_editor: LevelDataEditor
    start_editor: LevelStartEditor
    graphics_editor: LevelGraphicsEditor
    warp_editor: LevelWarpEditor
    info_editor: LevelInformationEditor

    def __init__(
        self,
        parent: QWidget,
        data: LevelDataState,
        start: LevelStartState,
        graphics: LevelGraphicsState,
        warp: LevelWarpState,
        info: LevelInformationState,
        level_bytes: bytearray,
        file_settings: FileSettings,
    ):
        super().__init__(parent)
        self.file_settings = file_settings

        self._tabbed_widget = QTabWidget(parent)

        self.data_editor = LevelDataEditor(self._tabbed_widget, data)
        self.start_editor = LevelStartEditor(self._tabbed_widget, start)
        self.graphics_editor = LevelGraphicsEditor(self._tabbed_widget, graphics)
        self.warp_editor = LevelWarpEditor(self._tabbed_widget, warp, file_settings=self.file_settings)
        self.info_editor = LevelInformationEditor(self._tabbed_widget, info)

        self._tabbed_widget.addTab(self.data_editor, "Level")
        self._tabbed_widget.addTab(self.start_editor, "Mario")
        self._tabbed_widget.addTab(self.graphics_editor, "Graphics")
        self._tabbed_widget.addTab(self.warp_editor, "Warping")
        self._tabbed_widget.addTab(self.info_editor, "Info")

        self.addWidget(self._tabbed_widget)

        self.header_bytes_label = QLabel()
        self.level_bytes = level_bytes

        self.addWidget(self.header_bytes_label, alignment=Qt.AlignCenter)  # type: ignore

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}({self.parent}, {self.data}. {self.start},"
            + f" {self.graphics}, {self.warp}, {self.info}, {self.file_settings})"
        )

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, HeaderDisplay)
            and self.data == other.data
            and self.start == other.start
            and self.graphics == other.graphics
            and self.warp == other.warp
            and self.info == other.info
        )

    @property
    def current_page(self) -> int:
        """
        The current page accessed by the user.

        Returns
        -------
        int
            The index of the current page accessed.
        """
        return self._tabbed_widget.currentIndex()

    @current_page.setter
    def current_page(self, page: int):
        self._tabbed_widget.setCurrentIndex(page)

    @property
    def data(self) -> LevelDataState:
        """
        Provides the data of the level.

        Returns
        -------
        LevelDataState
            The data of the level.
        """
        return self.data_editor.state

    @data.setter
    def data(self, data: LevelDataState):
        self.data_editor.state = data

    @property
    def start(self) -> LevelStartState:
        """
        Provides the start of the level.

        Returns
        -------
        LevelStartState
            The start of the level.
        """
        return self.start_editor.state

    @start.setter
    def start(self, start: LevelStartState):
        self.start_editor.state = start

    @property
    def graphics(self) -> LevelGraphicsState:
        """
        Provides the graphics of the level.

        Returns
        -------
        LevelGraphicsState
            The graphics of the level.
        """
        return self.graphics_editor.state

    @graphics.setter
    def graphics(self, graphics: LevelGraphicsState):
        self.graphics_editor.state = graphics

    @property
    def warp(self) -> LevelWarpState:
        """
        Provides the warp of the level.

        Returns
        -------
        LevelWarpState
            The warp of the level.
        """
        return self.warp_editor.state

    @warp.setter
    def warp(self, warp: LevelWarpState):
        self.warp_editor.state = warp

    @property
    def info(self) -> LevelInformationState:
        """
        Provides the info of the level.

        Returns
        -------
        LevelInformationState
            The info of the level.
        """
        return self.info_editor.level

    @info.setter
    def info(self, info: LevelInformationState):
        self.info_editor.state = info

    @property
    def level_bytes(self) -> bytearray:
        """
        Provides the bytes for the level header.

        Returns
        -------
        bytearray
            The bytes for the level header.
        """
        return self._level_bytes

    @level_bytes.setter
    def level_bytes(self, level_bytes: bytearray):
        self._level_bytes = level_bytes
        self.header_bytes_label.setText(" ".join(f"{number:0=#4X}"[2:] for number in level_bytes))
