return {
  'hrsh7th/cmp-buffer',
  'hrsh7th/cmp-path',
  'hrsh7th/cmp-cmdline',
  'hrsh7th/cmp-calc',
  'hrsh7th/cmp-emoji',
  {
    'petertriho/cmp-git',
    config = function()
      require("cmp_git").setup()
    end
  },

  'mattn/vim-goimports',
  {
    'kana/vim-operator-replace',
    dependencies = {
      'kana/vim-operator-user',
    },
  },
  'christoomey/vim-tmux-navigator',
  'dhruvasagar/vim-table-mode',
  'diepm/vim-rest-console',
  'simeji/winresizer',
  'tpope/vim-abolish',
  'thinca/vim-quickrun',
  'stefandtw/quickfix-reflector.vim',
  'rhysd/vim-go-impl',
  'tmux-plugins/vim-tmux-focus-events',
  'kamykn/spelunker.vim',
  'kamykn/popup-menu.nvim',
  'machakann/vim-sandwich',
  'vim-jp/vimdoc-ja',
  'ray-x/lsp_signature.nvim',
  {
    'tyru/operator-camelize.vim',
    dependencies = {
      'kana/vim-operator-user',
    },
  },
  {
    's1n7ax/nvim-window-picker',
    name = 'window-picker',
    event = 'VeryLazy',
    version = '2.*',
    config = function()
      require 'window-picker'.setup()
    end,
  },
  {
    "ggandor/leap.nvim",
    config = function() require("leap").set_default_keymaps() end
  },
  {
    "folke/trouble.nvim",
    requires = "nvim-tree/nvim-web-devicons",
    config = function()
      require("trouble").setup {
        -- your configuration comes here
        -- or leave it empty to use the default settings
        -- refer to the configuration section below
      }
    end
  },
  'rebelot/kanagawa.nvim',
  "smartpde/telescope-recent-files",
  'tpope/vim-dispatch',
  'kyoh86/vim-go-coverage',
  'onsails/lspkind.nvim',
  {
    'echasnovski/mini.nvim',
    version = '*',
    config = function()
      -- default settings
      require('mini.bufremove').setup({})
      require('mini.doc').setup({})
      require('mini.splitjoin').setup({})
      require('mini.trailspace').setup({})
      require('mini.basics').setup({})
      require('mini.align').setup({})
      require('mini.move').setup({})

      -- custom settings
    end
  },
  'sentriz/vim-print-debug',
  'chrisbra/unicode.vim',
}
