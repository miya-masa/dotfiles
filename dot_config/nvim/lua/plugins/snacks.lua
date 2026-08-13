-- herdr ペイン内（$TMUX 無し）では herdr-navigate へフォールバックする。
-- tmux 内では従来どおり vim-tmux-navigator を呼ぶ（挙動は変えない）。
-- terminal window 専用（win.keys）なので常に stopinsert を先頭に挟む
-- （既存 rhs の <C-\><C-n> に相当）。core.lua とは重複するが、ファイル跨ぎの
-- 共有モジュールにはしない（この変更のスコープ外）。
local function nav(wincmd_dir, herdr_dir, tmux_cmd)
  return function()
    vim.cmd("stopinsert")
    if vim.env.TMUX then
      vim.cmd(tmux_cmd)
      return
    end
    local w = vim.fn.winnr()
    vim.cmd("wincmd " .. wincmd_dir)
    if vim.fn.winnr() == w then
      vim.fn.jobstart({ "herdr-navigate", "--force", herdr_dir })
    end
  end
end

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
              [[  ___ ___ /\_\  __  __    ___             __  __ /\_\    ___ ___]],
              [[ /' __` __\/\ \/\ \/\ \  /'__`\   _______/\ \/\ \\/\ \ /' __` __`\]],
              [[/\ \/\ \/\ \ \ \ \ \_\ \/\ \L\.\_/\______\ \ \_/ |\ \ \/\ \/\ \/\ \]],
              [[\ \_\ \_\ \_\ \_\/`____ \ \__/.\_\/______/\ \___/  \ \_\ \_\ \_\ \_\]],
              [[ \/_/\/_/\/_/\/_/`/___/> \/__/\/_/         \/__/    \/_/\/_/\/_/\/_/]],
              [[                    /\___/]],
              [[                    \/__/]],
            }
            local max = 0
            for _, l in ipairs(lines) do
              if #l > max then
                max = #l
              end
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
            nav_h = { "<C-h>", nav("h", "left", "TmuxNavigateLeft"), desc = "Tmux Navigate Left", mode = "t" },
            nav_j = { "<C-j>", nav("j", "down", "TmuxNavigateDown"), desc = "Tmux Navigate Down", mode = "t" },
            nav_k = { "<C-k>", nav("k", "up", "TmuxNavigateUp"), desc = "Tmux Navigate Up", mode = "t" },
            nav_l = { "<C-l>", nav("l", "right", "TmuxNavigateRight"), desc = "Tmux Navigate Right", mode = "t" },
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
