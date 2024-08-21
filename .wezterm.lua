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

-- config.font = wezterm.font 'Monaspace Argon Var'
config.font_size = 11.0
config.font = wezterm.font_with_fallback({
  { family = "Moralerspace Neon HWNF", weight = "Regular" },
  { family = "PlemolJP Console NF", weight = "Medium" },
  { family = "HackGen Console NF", weight = "Regular" },
})

wezterm.on("gui-startup", function()
  local tab, pane, window = mux.spawn_window({})
  window:gui_window():maximize()
end)

-- and finally, return the configuration to wezterm
return config
