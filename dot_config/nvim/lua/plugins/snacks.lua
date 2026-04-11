return {
  {
    "snacks.nvim",
    keys = {
      {
        "<leader>dk",
        function()
          Snacks.terminal("lazydocker", { cwd = LazyVim.root() })
        end,
        desc = "Lazydocker (Root Dir)",
      },
    },
    opts = {
      animate = {
        enabled = false,
      },
      image = {
        doc = {
          inline = true,
          float = true,
          max_width = 80,
          max_height = 40,
        },
      },
      dashboard = {
        preset = {
          header = (function()
            local lines = {
              [[           __                                     __]],
              [[  ___ ___ /\_\  __  __     __             __  __ /\_\    ___ ___]],
              [[ /' __` __`\/\ \/\ \/\ \  /'__`\   _______/\ \/\ \\/\ \ /' __` __`\]],
              [[/\ \/\ \/\ \ \ \ \ \_\ \/\ \L\.\_/\______\ \ \_/ |\ \ \/\ \/\ \/\ \]],
              [[\ \_\ \_\ \_\ \_\/`____ \ \__/.\_\/______/\ \___/  \ \_\ \_\ \_\ \_\]],
              [[ \/_/\/_/\/_/\/_/`/___/> \/__/\/_/         \/__/    \/_/\/_/\/_/\/_/]],
              [[                    /\___/]],
              [[                    \/__/]],
            }
            local max = 0
            for _, l in ipairs(lines) do
              if #l > max then max = #l end
            end
            for i, l in ipairs(lines) do
              lines[i] = l .. string.rep(" ", max - #l)
            end
            return table.concat(lines, "\n")
          end)(),
        },
      },
      terminal = {
        win = {
          keys = {
            nav_h = { "<C-h>", [[<C-\><C-n><Cmd>TmuxNavigateLeft<CR>]], desc = "Tmux Navigate Left", mode = "t" },
            nav_j = { "<C-j>", [[<C-\><C-n><Cmd>TmuxNavigateDown<CR>]], desc = "Tmux Navigate Down", mode = "t" },
            nav_k = { "<C-k>", [[<C-\><C-n><Cmd>TmuxNavigateUp<CR>]], desc = "Tmux Navigate Up", mode = "t" },
            nav_l = { "<C-l>", [[<C-\><C-n><Cmd>TmuxNavigateRight<CR>]], desc = "Tmux Navigate Right", mode = "t" },
          },
        },
      },
      picker = {
        actions = {
          sidekick_send = function(...)
            return require("sidekick.cli.picker.snacks").send(...)
          end,
        },
        win = {
          input = {
            keys = {
              ["<c-b>"] = {
                "sidekick_send",
                mode = { "n", "i" },
              },
            },
          },
        },
      },
    },
  },
}
