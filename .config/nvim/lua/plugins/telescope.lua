local lga_actions = require("telescope-live-grep-args.actions")
require("telescope").setup {
  defaults = {
    vimgrep_arguments = {
      "rg",
      "--color=never",
      "--no-heading",
      "--with-filename",
      "--line-number",
      "--column",
      "--smart-case",
      "--no-ignore",
      "--hidden"
    }
  },
  extensions = {
    fzf = {
      fuzzy = true,                   -- false will only do exact matching
      override_generic_sorter = true, -- override the generic sorter
      override_file_sorter = true,    -- override the file sorter
      case_mode = "smart_case",       -- or "ignore_case" or "respect_case"
    },
    live_grep_args = {
      auto_quoting = true, -- enable/disable auto-quoting
      -- define mappings, e.g.
      mappings = {         -- extend mappings
        i = {
          ["<C-k>"] = lga_actions.quote_prompt(),
          ["<C-i>"] = lga_actions.quote_prompt({ postfix = " --iglob " }),
        },
      },
      -- ... also accepts theme settings, for example:
      -- theme = "dropdown", -- use dropdown theme
      -- theme = { }, -- use own theme spec
      -- layout_config = { mirror=true }, -- mirror preview pane
    }
  }
}
require("telescope").load_extension("live_grep_args")
require("telescope").load_extension("recent_files")
require("telescope").load_extension("fzf")
require('telescope').load_extension('neoclip')
vim.keymap.set('n', '<Leader><C-B>', ':Rooter<CR>:Telescope buffers<CR>')
vim.keymap.set("n", "<leader><C-R>", ":lua require('telescope').extensions.live_grep_args.live_grep_args()<CR>")
vim.keymap.set('n', '<Leader>rg', ':Telescope live_grep glob_pattern=')
vim.keymap.set('n', '<Leader><C-L>', ':Telescope grep_string<CR>')
vim.keymap.set('n', '<Leader><C-G>', ':Telescope git_files<CR>')
vim.keymap.set('n', '<Leader><C-Q>', ':Telescope quickfix<CR>')
vim.keymap.set('n', '<Leader>;', ':Telescope recent_files pick<CR>')
vim.keymap.set('n', '<Leader><C-Y>', ':Telescope neoclip<CR>')
vim.keymap.set('n', '<Leader><C-F>', ':lua require("telescope.builtin").find_files({hidden=true, find_command=rg})<CR>')
vim.keymap.set('n', '<Leader>f', ':Telescope frecency<CR>')
