from foundry.gui.settings import PydanticUserSettings, load_settings

MALFORMED_SETTINGS = """
{
    "block_transparency": true,
    "default_powerup": 0,
    "draw_autoscroll": false,
    "draw_expansion": false,
    "draw_grid": false,
    "draw_invisible_items": true,
    "draw_items_in_blocks": true,
    "draw_jump_on_objects": true,
    "draw_jumps": false,
    "draw_mario": true,
    "gui_style": "",
    "instaplay_arguments": "%f",
    "instaplay_emulator": "fceux",
    "object_scroll_enabled": false,
    "object_tooltip_enabled": true,
    "resize_mode": "LMB"
}
"""


def test_load_settings_validation_exception(tmp_path):
    settings_path = tmp_path / "test_setting.json"
    settings_path.write_text(MALFORMED_SETTINGS)

    assert PydanticUserSettings().to_user_settings() == load_settings(settings_path)
