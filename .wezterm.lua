-- Pull in the wezterm API
local wezterm = require("wezterm")
local mux = wezterm.mux

-- This table will hold the configuration.
local config = {}

-- In newer versions of wezterm, use the config_builder which will
-- help provide clearer error messages
if wezterm.config_builder then
  config = wezterm.config_builder()
end

-- This is where you actually apply your config choices

-- For example, changing the color scheme:
config.color_scheme = "Catppuccin Mocha"
config.use_ime = true
config.enable_wayland = false
config.window_background_opacity = 0.8

-- config.font = wezterm.font 'Monaspace Argon Var'
config.font_size = 11.0
config.font = wezterm.font_with_fallback({
  { family = "HackGen Console NF", weight = "Regular" },
  { family = "Moralerspace Neon HWNF", weight = "Regular" },
  { family = "PlemolJP Console NF", weight = "Medium" },
})

wezterm.on("gui-startup", function()
  local tab, pane, window = mux.spawn_window({})
  window:gui_window():maximize()
end)

config.window_frame = {
  -- The font used in the tab bar.
  -- Roboto Bold is the default; this font is bundled
  -- with wezterm.
  -- Whatever font is selected here, it will have the
  -- main font setting appended to it to pick up any
  -- fallback fonts you may have used there.
  font = wezterm.font({ family = "HackGen Console NF", weight = "Regular" }),

  -- The size of the font in the tab bar.
  -- Default to 10.0 on Windows but 12.0 on other systems
  font_size = 10.0,
}

-- and finally, return the configuration to wezterm
return config
