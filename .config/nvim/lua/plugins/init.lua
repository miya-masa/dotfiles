local ensure_packer = function()
  local fn = vim.fn
  local install_path = fn.stdpath('data')..'/site/pack/packer/start/packer.nvim'
  if fn.empty(fn.glob(install_path)) > 0 then
    fn.system({'git', 'clone', '--depth', '1', 'https://github.com/wbthomason/packer.nvim', install_path})
    vim.cmd [[packadd packer.nvim]]
    return true
  end
  return false
end

local packer_bootstrap = ensure_packer()

require('packer').startup(function(use)
  use 'wbthomason/packer.nvim'
  use 'AndrewRadev/splitjoin.vim'
  use 'sainnhe/gruvbox-material'
  use 'rebelot/kanagawa.nvim'
  use 'Shougo/vinarise.vim'
  use 'VincentCordobes/vim-translate'
  use 'airblade/vim-rooter'
  use 'aklt/plantuml-syntax'
  use 'bkad/CamelCaseMotion'
  use 'bronson/vim-trailing-whitespace'
  use 'christoomey/vim-tmux-navigator'
  use 'rhysd/vim-go-impl'
  use 'dhruvasagar/vim-table-mode'
  use 'diepm/vim-rest-console'
  use 'ggandor/leap.nvim'
  use 'APZelos/blamer.nvim'
  use 'windwp/nvim-autopairs'
  use {
    'nvim-telescope/telescope.nvim', tag = '0.1.x',
    requires = { {'nvim-lua/plenary.nvim'} }
  }
  use {'nvim-telescope/telescope-fzf-native.nvim', run = 'make' }
  use "folke/zen-mode.nvim"
  use 'junegunn/vim-easy-align'
  use 'kana/vim-operator-replace'
  use 'kana/vim-operator-user'
  use 'liuchengxu/vista.vim'
  use 'maxmellon/vim-jsx-pretty'
  use 'glepnir/dashboard-nvim'
  use 'lukas-reineke/indent-blankline.nvim'
  use {'raghur/vim-ghost', run = ':GhostInstall'}
  use 'nvim-lualine/lualine.nvim'
  use 'mfussenegger/nvim-dap'
  use 'simeji/winresizer'
  use 'sjl/gundo.vim'
  use 'stefandtw/quickfix-reflector.vim'
  use 'terryma/vim-expand-region'
  use 'thinca/vim-quickrun'
  use 'thinca/vim-zenspace'
  use 'tmux-plugins/vim-tmux-focus-events'
  use 'tpope/vim-abolish'
  use 'terrortylor/nvim-comment'
  use 'tpope/vim-dispatch'
  use 'TimUntersberger/neogit'
  use 'sindrets/diffview.nvim'
  use 'tpope/vim-markdown'
  use 'tpope/vim-repeat'
  use 'tpope/vim-surround'
  use 'tpope/vim-unimpaired'
  use 'tpope/vim-obsession'
  use 'vim-jp/vimdoc-ja'
  use 'vim-scripts/DrawIt'
  use 'kamykn/spelunker.vim'
  use 'kamykn/popup-menu.nvim'
  use 'airblade/vim-gitgutter'
  use 'tyru/open-browser.vim'
  use 'tyru/operator-camelize.vim'
  use { 'nvim-treesitter/nvim-treesitter', run = ':TSUpdate'}
  use 'nvim-treesitter/nvim-treesitter-textobjects'
  use 'kyoh86/vim-go-coverage'
  use 'neovim/nvim-lspconfig'
  use 'williamboman/nvim-lsp-installer'
  use 'hrsh7th/cmp-nvim-lsp'
  use 'hrsh7th/cmp-buffer'
  use 'hrsh7th/cmp-path'
  use 'hrsh7th/cmp-cmdline'
  use 'hrsh7th/cmp-calc'
  use 'hrsh7th/cmp-emoji'
  use 'hrsh7th/nvim-cmp'
  use 'uga-rosa/cmp-dictionary'
  use 'petertriho/cmp-git'
  use 'kyazdani42/nvim-web-devicons'
  use 'kyazdani42/nvim-tree.lua'
  use 'mattn/vim-goimports'
  use 'mattn/vim-goaddtags'
  use 'buoto/gotests-vim'
  use 'rhysd/vim-clang-format'
  use 'mustache/vim-mustache-handlebars'
  use 'iberianpig/tig-explorer.vim'
  use 'jose-elias-alvarez/null-ls.nvim'
  use 'nvim-lua/plenary.nvim'
  use 'liuchengxu/vista.vim'
  use 'vim-scripts/dbext.vim'
  use 'hrsh7th/cmp-vsnip'
  use 'hrsh7th/vim-vsnip'
  use 'hrsh7th/vim-vsnip-integ'
  use 'rafamadriz/friendly-snippets'
  use 'petobens/poet-v'
  use 'jsborjesson/vim-uppercase-sql'
  use 'jjo/vim-cue'
  use 'ray-x/lsp_signature.nvim'
  use 'antoinemadec/FixCursorHold.nvim'
  use 'nvim-neotest/neotest'
  use 'nvim-neotest/neotest-go'
  use 'nvim-neotest/neotest-python'
  use 'beauwilliams/focus.nvim'
  use 'AckslD/nvim-neoclip.lua'
  use 'onsails/lspkind.nvim'
  use 'deris/vim-rengbang'
  -- use 'tpope/vim-projectionist'
  use 'rgroli/other.nvim'
  use 'akinsho/git-conflict.nvim'
  use 'sentriz/vim-print-debug'
  use 'renerocksai/telekasten.nvim'
  use 'renerocksai/calendar-vim'
  use 'mzlogin/vim-markdown-toc'

  -- Automatically set up your configuration after cloning packer.nvim
  -- Put this at the end after all plugins
  if packer_bootstrap then
    require('packer').sync()
  end
end)

require("plugins.neogit")
require("plugins.nvim-comment")
require("plugins.nvim-tree")