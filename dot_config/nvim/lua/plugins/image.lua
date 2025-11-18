return {
  {
    "3rd/image.nvim",
    dependencies = {
      "nvim-lua/plenary.nvim",
    },
    config = function()
      require("image").setup({
        backend = "kitty", -- Ghosttyではこれで動く
        max_width = 80,
        max_height = 40,
        max_height_window_percentage = 50,
        max_width_window_percentage = 50,
        window_overlap_clear_enabled = true, -- 画像が重なったときに消去
        editor_only_render_when_focused = false,
        integrations = {
          markdown = {
            enabled = true,
            clear_in_insert_mode = true,
          },
          neorg = { enabled = true },
        },
      })
    end,
  },
}
