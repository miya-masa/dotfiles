-- herdr ペイン内（$TMUX 無し）では herdr-navigate へフォールバックする。
-- tmux 内では従来どおり vim-tmux-navigator を呼ぶ（挙動は変えない）。
-- term=true の場合のみ、terminal mode から抜けるための stopinsert を先頭に挟む
-- （既存 rhs の <C-\><C-n> に相当。normal mode の 5 本には無い）。
local function nav(wincmd_dir, herdr_dir, tmux_cmd, term)
  return function()
    if term then
      vim.cmd("stopinsert")
    end
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

-- <C-\> は縮退経路（tmux 無しなら <C-w>p）が他と形が違うため共通化しない。
local function nav_prev(tmux_cmd, term)
  return function()
    if term then
      vim.cmd("stopinsert")
    end
    if vim.env.TMUX then
      vim.cmd(tmux_cmd)
    else
      vim.cmd("wincmd p")
    end
  end
end

return {
  {
    "christoomey/vim-tmux-navigator",
    -- プラグイン自身の plugin/tmux_navigator.vim が既定でグローバルに
    -- <C-h/j/k/l/\> を再定義し、下の keys 定義（$TMUX 分岐）を上書きしてしまう
    -- （tmux 内では従来どおり TmuxNavigateLeft 等を呼ぶだけなので気付かなかった）。
    -- 無効化して keys 側のマッピングを常に有効にする。
    init = function()
      vim.g.tmux_navigator_no_mappings = 1
      -- 既定マッピングと同じブロックにある netrw workaround も一緒に無効化
      -- されるため、tmux 内の挙動を変えないよう明示的に復元する。
      vim.g.Netrw_UserMaps = { { "<C-l>", "<C-U>TmuxNavigateRight<cr>" } }
    end,
    cmd = {
      "TmuxNavigateLeft",
      "TmuxNavigateDown",
      "TmuxNavigateUp",
      "TmuxNavigateRight",
      "TmuxNavigatePrevious",
      "TmuxNavigatorProcessList",
    },
    keys = {
      { "<c-h>", nav("h", "left", "TmuxNavigateLeft") },
      { "<c-j>", nav("j", "down", "TmuxNavigateDown") },
      { "<c-k>", nav("k", "up", "TmuxNavigateUp") },
      { "<c-l>", nav("l", "right", "TmuxNavigateRight") },
      { "<c-\\>", nav_prev("TmuxNavigatePrevious") },

      -- Terminal
      { "<c-h>", nav("h", "left", "TmuxNavigateLeft", true), mode = "t" },
      { "<c-j>", nav("j", "down", "TmuxNavigateDown", true), mode = "t" },
      { "<c-k>", nav("k", "up", "TmuxNavigateUp", true), mode = "t" },
      { "<c-l>", nav("l", "right", "TmuxNavigateRight", true), mode = "t" },
      { "<c-\\>", nav_prev("TmuxNavigatePrevious", true), mode = "t" },
    },
  },
  {
    "johmsalas/text-case.nvim",
    config = function()
      require("textcase").setup({})
    end,
    keys = {
      { "ga.", "<cmd>TextCaseOpenTelescope<CR>", mode = "n", desc = "Text Case" },
      { "ga.", "<cmd>TextCaseOpenTelescope<CR>", mode = "v", desc = "Text Case" },
    },
    cmd = {
      "Subs",
      "TextCaseOpenTelescope",
      "TextCaseOpenTelescopeQuickChange",
      "TextCaseOpenTelescopeLSPChange",
      "TextCaseStartReplacingCommand",
    },
  },
  {
    "esmuellert/codediff.nvim",
    cmd = "CodeDiff",
  },
  {
    "vim-jp/vimdoc-ja",
    event = "CmdlineEnter",
  },
  {
    "jbyuki/venn.nvim",
    keys = {
      { "<leader>tv", ":lua Toggle_venn()<CR>", noremap = true, desc = "Toggle Venn" },
    },
    config = function()
      function _G.Toggle_venn()
        local venn_enabled = vim.inspect(vim.b.venn_enabled)
        if venn_enabled == "nil" then
          vim.b.venn_enabled = true
          vim.cmd([[setlocal ve=all]])
          vim.api.nvim_buf_set_keymap(0, "n", "J", "<C-v>j:VBox<CR>", { noremap = true })
          vim.api.nvim_buf_set_keymap(0, "n", "K", "<C-v>k:VBox<CR>", { noremap = true })
          vim.api.nvim_buf_set_keymap(0, "n", "L", "<C-v>l:VBox<CR>", { noremap = true })
          vim.api.nvim_buf_set_keymap(0, "n", "H", "<C-v>h:VBox<CR>", { noremap = true })
          vim.api.nvim_buf_set_keymap(0, "v", "<CR>", ":VBox<CR>", { noremap = true })
          print("venn on")
        else
          vim.cmd([[setlocal ve=]])
          vim.api.nvim_buf_del_keymap(0, "n", "J")
          vim.api.nvim_buf_del_keymap(0, "n", "K")
          vim.api.nvim_buf_del_keymap(0, "n", "L")
          vim.api.nvim_buf_del_keymap(0, "n", "H")
          vim.api.nvim_buf_del_keymap(0, "v", "<CR>")
          vim.b.venn_enabled = nil
          print("venn off")
        end
      end
    end,
  },
  {
    "RaafatTurki/hex.nvim",
    cmd = { "HexDump", "HexAssemble", "HexToggle" },
    opts = {},
  },
  {
    "Wansmer/treesj",
    keys = { "<space>m", "<space>j", "<space>s" },
    dependencies = { "nvim-treesitter/nvim-treesitter" },
    opts = {},
  },
}
