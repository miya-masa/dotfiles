" Enable plugin {{{
let data_dir = has('nvim') ? stdpath('data') . '/site' : '~/.vim'
if empty(glob(data_dir . '/autoload/plug.vim'))
  silent execute '!curl -fLo '.data_dir.'/autoload/plug.vim --create-dirs  https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim'
  autocmd VimEnter * PlugInstall --sync | source $MYVIMRC
endif
" }}}
" VimPlug Start {{{
call plug#begin('~/.vim/plugged')
Plug 'AndrewRadev/splitjoin.vim'
Plug 'sainnhe/gruvbox-material'
Plug 'rebelot/kanagawa.nvim'
Plug 'Shougo/vinarise.vim'
" Plug 'SirVer/ultisnips'
Plug 'VincentCordobes/vim-translate'
Plug 'airblade/vim-rooter'
Plug 'aklt/plantuml-syntax'
Plug 'bkad/CamelCaseMotion'
Plug 'bronson/vim-trailing-whitespace'
Plug 'christoomey/vim-tmux-navigator'
Plug 'rhysd/vim-go-impl'
Plug 'dhruvasagar/vim-table-mode'
Plug 'diepm/vim-rest-console'
" Plug 'easymotion/vim-easymotion'
Plug 'ggandor/leap.nvim'
Plug 'APZelos/blamer.nvim'
Plug 'edkolev/tmuxline.vim'
Plug 'flazz/vim-colorschemes'
Plug 'honza/vim-snippets'
Plug 'iamcco/markdown-preview.nvim', { 'do': 'cd app && yarn install'  }
Plug 'windwp/nvim-autopairs'
" Plug 'junegunn/fzf', { 'dir': '~/.fzf', 'do': './install --all' }
" Plug 'junegunn/fzf.vim'
Plug 'nvim-telescope/telescope.nvim', { 'tag': '0.1.0' }
Plug 'nvim-telescope/telescope-fzf-native.nvim', { 'do': 'make' }
Plug 'junegunn/goyo.vim'
Plug 'junegunn/gv.vim'
Plug 'junegunn/vim-easy-align'
Plug 'kana/vim-operator-replace'
Plug 'kana/vim-operator-user'
Plug 'liuchengxu/vista.vim'
Plug 'maxmellon/vim-jsx-pretty'
Plug 'mhinz/vim-startify'
Plug 'miya-masa/gotest-compiler-vim'
Plug 'lukas-reineke/indent-blankline.nvim'
Plug 'raghur/vim-ghost', {'do': ':GhostInstall'}
Plug 'sebdah/vim-delve'
Plug 'nvim-lualine/lualine.nvim'
Plug 'simeji/winresizer'
Plug 'sjl/gundo.vim'
Plug 'stefandtw/quickfix-reflector.vim'
Plug 'terryma/vim-expand-region'
Plug 'thinca/vim-quickrun'
Plug 'thinca/vim-zenspace'
Plug 'tmux-plugins/vim-tmux-focus-events'
Plug 'tpope/vim-abolish'
" Plug 'tpope/vim-commentary'
Plug 'terrortylor/nvim-comment'
Plug 'tpope/vim-dispatch'
" Plug 'tpope/vim-fugitive'
Plug 'TimUntersberger/neogit'
Plug 'sindrets/diffview.nvim'
Plug 'tpope/vim-markdown'
Plug 'tpope/vim-projectionist'
Plug 'tpope/vim-repeat'
Plug 'tpope/vim-surround'
Plug 'tpope/vim-unimpaired'
Plug 'tpope/vim-obsession'
Plug 'vim-jp/vimdoc-ja'
Plug 'vim-scripts/DrawIt'
Plug 'kamykn/spelunker.vim'
Plug 'kamykn/popup-menu.nvim'
Plug 'airblade/vim-gitgutter'
Plug 'tyru/open-browser.vim'
Plug 'tyru/operator-camelize.vim'
Plug 'nvim-treesitter/nvim-treesitter', {'do': ':TSUpdate'}  " We recommend updating the parsers on update
Plug 'nvim-treesitter/nvim-treesitter-textobjects'
Plug 'kyoh86/vim-go-coverage'
Plug 'mzlogin/vim-markdown-toc'
Plug 'neovim/nvim-lspconfig'
Plug 'williamboman/nvim-lsp-installer'
Plug 'hrsh7th/cmp-nvim-lsp'
Plug 'hrsh7th/cmp-buffer'
Plug 'hrsh7th/cmp-path'
Plug 'hrsh7th/cmp-cmdline'
Plug 'hrsh7th/cmp-calc'
Plug 'hrsh7th/cmp-emoji'
Plug 'hrsh7th/nvim-cmp'
" Plug 'quangnguyen30192/cmp-nvim-ultisnips'
Plug 'uga-rosa/cmp-dictionary'
Plug 'petertriho/cmp-git'
" requires
Plug 'kyazdani42/nvim-web-devicons' " for file icons
Plug 'kyazdani42/nvim-tree.lua'
Plug 'mattn/vim-goimports'
Plug 'mattn/vim-goaddtags'
Plug 'buoto/gotests-vim'
Plug 'rhysd/vim-clang-format'
Plug 'mustache/vim-mustache-handlebars'
Plug 'iberianpig/tig-explorer.vim'
Plug 'jose-elias-alvarez/null-ls.nvim'
Plug 'nvim-lua/plenary.nvim'
Plug 'liuchengxu/vista.vim'
Plug 'vim-scripts/dbext.vim'
Plug 'hrsh7th/cmp-vsnip'
Plug 'hrsh7th/vim-vsnip'
Plug 'hrsh7th/vim-vsnip-integ'
Plug 'rafamadriz/friendly-snippets'
Plug 'petobens/poet-v'
Plug 'jsborjesson/vim-uppercase-sql'
Plug 'jjo/vim-cue'
Plug 'ray-x/lsp_signature.nvim'
Plug 'puremourning/vimspector'
Plug 'antoinemadec/FixCursorHold.nvim'
Plug 'nvim-neotest/neotest'
Plug 'nvim-neotest/neotest-go'
Plug 'nvim-neotest/neotest-python'
Plug 'beauwilliams/focus.nvim'
Plug 'AckslD/nvim-neoclip.lua'
Plug 'onsails/lspkind.nvim'
Plug 'deris/vim-rengbang'
Plug 'rgroli/other.nvim'
Plug 'akinsho/git-conflict.nvim'
Plug 'sentriz/vim-print-debug'
Plug 'renerocksai/telekasten.nvim'
Plug 'renerocksai/calendar-vim'
Plug 'mzlogin/vim-markdown-toc'


call plug#end()
set completeopt=menu,menuone,noselect

lua << EOF
local signs = { Error = "", Warn = "", Hint = "", Info = "" }

for type, icon in pairs(signs) do
  local hl = "DiagnosticSign" .. type
  vim.fn.sign_define(hl, { text = icon, texthl = hl, numhl = hl })
end
EOF

lua << EOF
require('nvim_comment').setup()
EOF

lua << EOF
require('neogit').setup {
  integrations = {
    diffview = true
  }
}
EOF

" {{{ neotest
lua << EOF
require("neotest").setup({
  adapters = {
    require("neotest-python"),
    require("neotest-go")({
      experimental = {
        test_table = true,
      },
      args = { "-count=1", "-timeout=60s" , "-tags=integration"}
    })
  },
  floating = {
    max_height = 0.9,
    max_width = 0.9,
  },
  icons = {
    failed = "X",
    final_child_indent = " ",
    final_child_prefix = "╰",
    non_collapsible = "─",
    passed = "O",
    running = "-",
    running_animated = { "/", "|", "\\", "-", "/", "|", "\\", "-" },
    skipped = "-",
    unknown = "-"
  },
})
EOF
" }}}

" focus {{{ 
lua << EOF
require("focus").setup()
EOF
" }}}

lua << EOF
local null_ls = require("null-ls")

-- register any number of sources simultaneously
local sources = {
    null_ls.builtins.formatting.prettier,
    null_ls.builtins.diagnostics.golangci_lint,
    null_ls.builtins.diagnostics.hadolint,
    null_ls.builtins.diagnostics.markdownlint,
    null_ls.builtins.diagnostics.pyproject_flake8,
    null_ls.builtins.formatting.isort,
    null_ls.builtins.formatting.black,
}

null_ls.setup({ sources = sources })
EOF

lua <<EOF
cfg = {}
require "lsp_signature".setup(cfg)
EOF


lua << EOF
require('nvim-autopairs').setup{}
-- default mappings
local list = {
  { key = {"<CR>", "o", "<2-LeftMouse>"}, action = "edit" },
  { key = "<C-e>",                        action = "" },
  { key = {"O"},                          action = "edit_no_picker" },
  { key = {"<2-RightMouse>", "<C-]>"},    action = "cd" },
  { key = "<C-v>",                        action = "vsplit" },
  { key = "<C-x>",                        action = "split" },
  { key = "<C-t>",                        action = "tabnew" },
  { key = "<",                            action = "prev_sibling" },
  { key = ">",                            action = "next_sibling" },
  { key = "P",                            action = "parent_node" },
  { key = "<BS>",                         action = "close_node" },
  { key = "<Tab>",                        action = "preview" },
  { key = "K",                            action = "first_sibling" },
  { key = "J",                            action = "last_sibling" },
  { key = "I",                            action = "toggle_ignored" },
  { key = "H",                            action = "toggle_dotfiles" },
  { key = "R",                            action = "refresh" },
  { key = "a",                            action = "create" },
  { key = "d",                            action = "remove" },
  { key = "D",                            action = "trash" },
  { key = "r",                            action = "rename" },
  { key = "<C-r>",                        action = "full_rename" },
  { key = "x",                            action = "cut" },
  { key = "c",                            action = "copy" },
  { key = "p",                            action = "paste" },
  { key = "y",                            action = "copy_name" },
  { key = "Y",                            action = "copy_path" },
  { key = "gy",                           action = "copy_absolute_path" },
  { key = "[c",                           action = "prev_git_item" },
  { key = "]c",                           action = "next_git_item" },
  { key = "-",                            action = "dir_up" },
  { key = "s",                            action = "system_open" },
  { key = "q",                            action = "close" },
  { key = "g?",                           action = "toggle_help" },
  { key = 'W',                            action = "collapse_all" },
  { key = "S",                            action = "search_node" },
  { key = ".",                            action = "run_file_command" },
  { key = "<C-k>",                        action = "" },
  { key = "U",                            action = "toggle_custom" },
}
require'nvim-tree'.setup {
  view = {
    width = '20%',
    mappings = {
      custom_only = false,
      list = list
    },
  },
}

local nvim_lsp = require('lspconfig')

local opts = { noremap=true, silent=true }
vim.api.nvim_set_keymap('n', '<space>e', '<cmd>lua vim.diagnostic.open_float()<CR>', opts)
vim.api.nvim_set_keymap('n', '[g', '<cmd>lua vim.diagnostic.goto_prev()<CR>', opts)
vim.api.nvim_set_keymap('n', ']g', '<cmd>lua vim.diagnostic.goto_next()<CR>', opts)
vim.api.nvim_set_keymap('n', '<space>q', '<cmd>lua vim.diagnostic.setloclist()<CR>', opts)

-- Use an on_attach function to only map the following keys
-- after the language server attaches to the current buffer

local on_attacher = function(enable_format)
  local on_attach = function(client, bufnr)

    client.server_capabilities.document_formatting = enable_format
    client.server_capabilities.document_range_formatting = enable_format

    -- Enable completion triggered by <c-x><c-o>
    vim.api.nvim_buf_set_option(bufnr, 'omnifunc', 'v:lua.vim.lsp.omnifunc')

    -- Mappings.
    -- See `:help vim.lsp.*` for documentation on any of the below functions
    vim.api.nvim_buf_set_keymap(bufnr, 'n', '<Leader>gD', '<cmd>lua vim.lsp.buf.declaration()<CR>', opts)
    vim.api.nvim_buf_set_keymap(bufnr, 'n', '<Leader>gd', '<cmd>lua vim.lsp.buf.definition()<CR>', opts)
    vim.api.nvim_buf_set_keymap(bufnr, 'n', 'K', '<cmd>lua vim.lsp.buf.hover()<CR>', opts)
    vim.api.nvim_buf_set_keymap(bufnr, 'n', '<Leader>gi', '<cmd>lua vim.lsp.buf.implementation()<CR>', opts)
    vim.api.nvim_buf_set_keymap(bufnr, 'n', '<Leader><C-k>', '<cmd>lua vim.lsp.buf.signature_help()<CR>', opts)
    vim.api.nvim_buf_set_keymap(bufnr, 'n', '<space>wa', '<cmd>lua vim.lsp.buf.add_workspace_folder()<CR>', opts)
    vim.api.nvim_buf_set_keymap(bufnr, 'n', '<space>wr', '<cmd>lua vim.lsp.buf.remove_workspace_folder()<CR>', opts)
    vim.api.nvim_buf_set_keymap(bufnr, 'n', '<space>wl', '<cmd>lua print(vim.inspect(vim.lsp.buf.list_workspace_folders()))<CR>', opts)
    vim.api.nvim_buf_set_keymap(bufnr, 'n', '<Leader>D', '<cmd>lua vim.lsp.buf.type_definition()<CR>', opts)
    vim.api.nvim_buf_set_keymap(bufnr, 'n', '<Leader>rn', '<cmd>lua vim.lsp.buf.rename()<CR>', opts)
    vim.api.nvim_buf_set_keymap(bufnr, 'n', '<Leader>ca', '<cmd>lua vim.lsp.buf.code_action()<CR>', opts)
    vim.api.nvim_buf_set_keymap(bufnr, 'n', '<Leader>gr', '<cmd>lua vim.lsp.buf.references()<CR>', opts)
    vim.api.nvim_buf_set_keymap(bufnr, 'n', '<Leader><C-f>', '<cmd>lua vim.lsp.buf.format()<CR>', opts)
  end
  return on_attach
end

-- Use a loop to conveniently call 'setup' on multiple servers and
-- map buffer local keybindings when the language server attaches
  -- Setup nvim-cmp.
  local cmp = require'cmp'

  cmp.setup({
    snippet = {
      -- REQUIRED - you must specify a snippet engine
      expand = function(args)
        vim.fn["vsnip#anonymous"](args.body) -- For `vsnip` users.
        -- require('luasnip').lsp_expand(args.body) -- For `luasnip` users.
        -- vim.fn["UltiSnips#Anon"](args.body) -- For `ultisnips` users.
        -- require'snippy'.expand_snippet(args.body) -- For `snippy` users.
      end,
    },
    mapping = {
      ['<C-e>'] = cmp.mapping({
        i = cmp.mapping.abort(),
        c = cmp.mapping.close(),
      }),
      ['<C-y>'] = cmp.mapping.confirm({ select = true }), -- Specify `cmp.config.disable` if you want to remove the default `<C-y>` mapping.
      ['<CR>'] = cmp.mapping.confirm({ select = true }),
      ['<C-n>'] = cmp.mapping({
          c = function()
              if cmp.visible() then
                  cmp.select_next_item()
              else
                  vim.api.nvim_feedkeys(t('<Down>'), 'n', true)
              end
          end,
          i = function(fallback)
              if cmp.visible() then
                  cmp.select_next_item()
              else
                  fallback()
              end
          end
      }),
      ['<C-p>'] = cmp.mapping({
          c = function()
              if cmp.visible() then
                  cmp.select_prev_item()
              else
                  vim.api.nvim_feedkeys(t('<Up>'), 'n', true)
              end
          end,
          i = function(fallback)
              if cmp.visible() then
                  cmp.select_prev_item()
              else
                  fallback()
              end
          end
      }),
    },
    sources = cmp.config.sources({
      { name = 'nvim_lsp' },
      { name = 'git' },
      -- { name = 'ultisnips'}, -- For ultisnips users.
      { name = 'vsnip'},
      { name = 'buffer' },
      { name = 'path' },
      { name = 'calc' },
      { name = 'dictionary', keyword_length = 2 },
      { name = 'emoji' },
      })
  })

  -- Use buffer source for `/`.
  cmp.setup.cmdline('/', {
    sources = {
      { name = 'buffer' }
    }
  })

  -- Use cmdline & path source for ':'.
  cmp.setup.cmdline(':', {
    sources = cmp.config.sources({
      { name = 'path' }
    }, {
      { name = 'cmdline' }
    })
  })

  cmp.setup.preselect = cmp.PreselectMode.None

-- Setup cmp dictionary
require("cmp_dictionary").setup({
    dic = {
        ["*"] = "/usr/share/dict/words",
    },
    -- The following are default values, so you don't need to write them if you don't want to change them
    exact = 2,
    async = false,
    capacity = 5,
    debug = false,
})

--  Setup lspconfig.
local capabilities = require('cmp_nvim_lsp').default_capabilities(vim.lsp.protocol.make_client_capabilities())
capabilities.textDocument.completion.completionItem.snippetSupport = true

local lsp_installer = require("nvim-lsp-installer")
lsp_installer.on_server_ready(function(server)
    local opts = {}

    -- (optional) Customize the options passed to the server
    if server.name == "gopls" then
        opts.settings = {
          gopls = {
            buildFlags = {"-tags=integration"},
            usePlaceholders = true,
            gofumpt = true,
          }
        }
    end
    if server.name == "tsserver"
      or server.name == "pyright"
      or server.name == "golangci_lint_ls"
      or server.name == "yamlls"
    then
      opts.on_attach = on_attacher(false)
    else
      opts.on_attach = on_attacher(true)
    end
    opts.capabilities = capabilities

    -- This setup() function is exactly the same as lspconfig's setup function.
    -- Refer to https://github.com/neovim/nvim-lspconfig/blob/master/ADVANCED_README.md
    server:setup(opts)
end)

local lspkind = require('lspkind')
cmp.setup {
  formatting = {
    format = lspkind.cmp_format({
      mode = 'symbol', -- show only symbol annotations
      maxwidth = 50, -- prevent the popup from showing more than provided characters (e.g 50 will not show more than 50 characters)

      -- The function below will be called before any actual modifications from lspkind
      -- so that you can provide more controls on popup customization. (See [#30](https://github.com/onsails/lspkind-nvim/pull/30))
      before = function (entry, vim_item)
        return vim_item
      end
    })
  }
}

EOF

lua <<EOF
require'nvim-treesitter.configs'.setup {
  textobjects = {
    move = {
      enable = true,
      set_jumps = true, -- whether to set jumps in the jumplist
      goto_next_start = {
        ["]m"] = "@function.outer",
        ["]]"] = "@class.outer",
      },
      goto_next_end = {
        ["]M"] = "@function.outer",
        ["]["] = "@class.outer",
      },
      goto_previous_start = {
        ["[m"] = "@function.outer",
        ["[["] = "@class.outer",
      },
      goto_previous_end = {
        ["[M"] = "@function.outer",
        ["[]"] = "@class.outer",
      },
    },
    select = {
      enable = true,

      -- Automatically jump forward to textobj, similar to targets.vim
      lookahead = true,

      keymaps = {
        -- You can use the capture groups defined in textobjects.scm
        ["af"] = "@function.outer",
        ["if"] = "@function.inner",
        ["ac"] = "@class.outer",
        ["ic"] = "@class.inner",
      },
    },
  },
}
EOF

lua <<EOF
require'nvim-treesitter.configs'.setup {
  -- One of "all" (parsers with maintainers), or a list of languages
  ensure_installed = "all",

  -- Install languages synchronously (only applied to `ensure_installed`)
  sync_install = false,

  highlight = {
    -- `false` will disable the whole extension
    enable = true,

    -- Setting this to true will run `:h syntax` and tree-sitter at the same time.
    -- Set this to `true` if you depend on 'syntax' being enabled (like for indentation).
    -- Using this option may slow down your editor, and you may see some duplicate highlights.
    -- Instead of true it can also be a list of languages
    additional_vim_regex_highlighting = false,
  },
}
EOF


" }}}
" Plugin UltiSnips {{{
let g:UltiSnipsSnippetDirectories=["UltiSnips", "~/.config/nvim/UltiSnips", "UltiSnips_local"]
let g:UltiSnipsExpandTrigger="<C-l>"
let g:UltiSnipsEditSplit="vertical"
" }}}
" VimRestConsole {{{
let g:vrc_curl_opts = {
      \ '-b': '/tmp/cookie.txt',
      \ '-c': '/tmp/cookie.txt',
      \ '-L': '',
      \ '-i': '',
      \ '--max-time': 60
      \}
let g:vrc_auto_format_response_enabled = 1
let g:vrc_show_command = 1
let g:vrc_response_default_content_type = 'application/json'
let g:vrc_auto_format_response_patterns = {
      \ 'json': 'jq "."',
      \ 'xml': 'tidy -xml -i -'
      \}
let g:vrc_trigger = '<Leader><C-o>'
" }}}
" CamelCaseMotion {{{
let g:camelcasemotion_key = ','
" EmmetPlugin {{{
let g:user_emmet_leader_key='<C-t>'
" }}}
" vim-json {{{
let g:vim_json_syntax_conceal = 0
" }}}
lua << END
require'lualine'.setup {
  options = {
    -- theme = 'gruvbox-material'
    theme = 'kanagawa'
  }
}
END
function! NearestMethodOrFunction() abort
  return get(b:, 'vista_nearest_method_or_function', '')
endfunction
"
" }}}
" tmuxline {{{
let g:tmuxline_powerline_separators = 1
let g:tmuxline_preset = {
      \'a'    : '#S',
      \'b'    : ['#[fg=green,bg=default,bright]#(tmux-mem-cpu-load -a 0 -m 2 --interval 5) '],
      \'c'    : ['#(uptime | cut -d " " -f 1,2,3)','#(whoami)'],
      \'win'  : ['#I', '#W'],
      \'cwin' : ['#I', '#W', '#F'],
      \'x'    : ['Batt: #{battery_percentage}'],
      \'y'    : ['%Y/%m/%d %H:%M'],
      \'z'    : '#H'}
let g:tmuxline_separators = {
      \ 'left' : '',
      \ 'left_alt': '>',
      \ 'right' : '',
      \ 'right_alt' : '<',
      \ 'space' : ' '}

" }}}
" vim-notes {{{
let g:notes_directories = ['~/work/Notes']
let g:notes_suffix = '.md'
" }}}
" QuickRun {{{
let g:quickrun_config = {
\}
augroup rust_quickrun
  au!
  autocmd BufNewFile,BufRead *.rs let g:quickrun_config.rust = {'exec' : 'cargo run'}
augroup END
" }}}
" mhinz/vim-startify {{{
" startify
let g:startify_files_number = 5
let g:startify_lists = [
      \ { 'type': 'files',     'header': ['   MRU']            },
      \ { 'type': 'dir',       'header': ['   MRU '. getcwd()] },
      \ { 'type': 'sessions',  'header': ['   Sessions']       },
      \ { 'type': 'bookmarks', 'header': ['   Bookmarks']      },
      \ { 'type': 'commands',  'header': ['   Commands']       },
      \ ]
let g:startify_bookmarks = ['~/.config/nvim/init.vim']

function! s:filter_header(lines) abort
  let longest_line   = max(map(copy(a:lines), 'len(v:val)'))
  let centered_lines = map(copy(a:lines),
        \ 'repeat(" ", (&columns / 2) - (longest_line / 2)) . v:val')
  return centered_lines
endfunction

let g:startify_custom_header = s:filter_header([
      \ '           _ ',
      \ ' _ __ ___ (_)_   _  __ _       _ __ ___   __ _ ___  __ _  ',
      \ '| `_ ` _ \| | | | |/ _` |_____| `_ ` _ \ / _` / __|/ _` | ',
      \ '| | | | | | | |_| | (_| |_____| | | | | | (_| \__ \ (_| | ',
      \ '|_| |_| |_|_|\__, |\__,_|     |_| |_| |_|\__,_|___/\__,_| ',
      \ '             |___/ ',
      \ '                  __     _____ __  __  ',
      \ '                  \ \   / /_ _|  \/  | ',
      \ '                   \ \ / / | || |\/| | ',
      \ '                    \ V /  | || |  | | ',
      \ '                     \_/  |___|_|  |_| ',
      \ ])

" }}}
" VincentCordobes/vim-translate {{{
let g:translate#default_languages = {
      \ 'en': 'ja',
      \ 'ja': 'en'
      \ }
" }}}
" {{{ buoto/gotests-vim
let g:gotests_template = "testify"
" }}}
" {{{ sjl/gundo
let g:gundo_prefer_python3=1
" }}}
" {{{ Plug 'janko/vim-test'
let test#strategy = "dispatch"
let test#go#gotest#options = {
  \ 'nearest': '-count=1 -timeout=10s',
  \ 'file':    '-count=1 -timeout=30s',
  \ 'suite':   '-count=1 -timeout=2m',
\}
" }}}
"  Plug 'kana/vim-operator-replace' {{{
nmap ! <Plug>(operator-replace)
" }}}
"  Plug 'tpop/projectionist' {{{
let g:projectionist_ignore_quickrun=1
let g:projectionist_heuristics = {
      \ "*.go": {
      \   "*_test.go": {"type": "test", "alternate": "{}.go"},
      \   "*.go": {"type": "source", "alternate": "{}_test.go"}
      \  },
      \ "pyproject.toml": {
      \   "*.py": {"type": "source", "alternate": "tests/{dirname}/test_{basename}.py"}
      \  }
      \ }
" }}}
" vim-ghost {{{
function! s:SetupGhostBuffer()
  set ft=markdown
endfunction

augroup vim-ghost
    au!
    au User vim-ghost#connected call s:SetupGhostBuffer()
augroup END

" }}}
" Plug 'airblade/vim-rooter' {{{
let g:rooter_manual_only = 1
" }}}
" Plug 'tpope/vim-markdown' {{{
let g:markdown_fenced_languages = ['plantuml', 'go', 'java', 'bash=sh']
" }}}
" Plug 'indent' {{{

lua << EOF
require("indent_blankline").setup {
    char = "|",
    filetype_exclude = {"help", "startify", "dirvish", "no ft", "fzf", 'NvimTree', 'markdown'}
}
EOF

" }}}
" Plug 'indent' {{{
if filereadable(expand('~/.dbext_profile'))
    source ~/.dbext_profile
endif
" }}}

command! -bang -nargs=* Rg
  \ call fzf#vim#grep(
  \   'rg --column --line-number --no-heading --color=always --hidden --iglob ''!.git'' --smart-case -- '.shellescape(<q-args>), 1,
  \   fzf#vim#with_preview(), <bang>0)

" }}}
"
" Plug 'iamcco/markdown-preview.nvim'{{{
let g:mkdp_open_to_the_world = 1
let g:mkdp_port = '39999'
let g:mkdp_echo_preview_url = 1
let g:mkdp_preview_options = {
      \ 'uml': {
      \  'server': 'http://plantuml-server.internal:8989'
      \ },
    \ }
" }}}
let g:python3_host_prog = $HOME . '/.pyenv/shims/python'

" {{{ leap
lua require('leap').add_default_mappings()
" }}}

" NOTE: You can use other key to expand snippet.
" {{{ vsnip
" Expand
imap <expr> <C-y>   vsnip#expandable()  ? '<Plug>(vsnip-expand)'         : '<C-y>'
smap <expr> <C-y>   vsnip#expandable()  ? '<Plug>(vsnip-expand)'         : '<C-y>'

" Expand or jump
imap <expr> <C-j>   vsnip#available(1)  ? '<Plug>(vsnip-expand-or-jump)' : '<C-j>'
smap <expr> <C-j>   vsnip#available(1)  ? '<Plug>(vsnip-expand-or-jump)' : '<C-j>'

" Jump forward or backward
imap <expr> <Tab>   vsnip#jumpable(1)   ? '<Plug>(vsnip-jump-next)'      : '<Tab>'
smap <expr> <Tab>   vsnip#jumpable(1)   ? '<Plug>(vsnip-jump-next)'      : '<Tab>'
imap <expr> <S-Tab> vsnip#jumpable(-1)  ? '<Plug>(vsnip-jump-prev)'      : '<S-Tab>'
smap <expr> <S-Tab> vsnip#jumpable(-1)  ? '<Plug>(vsnip-jump-prev)'      : '<S-Tab>'

" Select or cut text to use as $TM_SELECTED_TEXT in the next snippet.
" See https://github.com/hrsh7th/vim-vsnip/pull/50
" nmap        s   <Plug>(vsnip-select-text)
" xmap        s   <Plug>(vsnip-select-text)
" nmap        S   <Plug>(vsnip-cut-text)
" xmap        S   <Plug>(vsnip-cut-text)

" If you want to use snippet for multiple filetypes, you can `g:vsnip_filetypes` for it.
let g:vsnip_filetypes = {}
let g:vsnip_filetypes.javascriptreact = ['javascript']
let g:vsnip_filetypes.typescriptreact = ['typescript']
" }}}
"
"
lua << EOF
require('telescope').load_extension('fzf')
EOF

" neoclip {{{
lua << EOF
require('neoclip').setup()
require('telescope').load_extension('neoclip')
EOF
" }}} focus

"""
lua << END
local home = vim.fn.expand("~/zettelkasten")
-- NOTE for Windows users:
-- - don't use Windows
-- - try WSL2 on Windows and pretend you're on Linux
-- - if you **must** use Windows, use "/Users/myname/zettelkasten" instead of "~/zettelkasten"
-- - NEVER use "C:\Users\myname" style paths
-- - Using `vim.fn.expand("~/zettelkasten")` should work now but mileage will vary with anything outside of finding and opening files
require('telekasten').setup({
    home         = home,

    -- if true, telekasten will be enabled when opening a note within the configured home
    take_over_my_home = true,

    -- auto-set telekasten filetype: if false, the telekasten filetype will not be used
    --                               and thus the telekasten syntax will not be loaded either
    auto_set_filetype = true,

    -- dir names for special notes (absolute path or subdir name)
    dailies      = home .. '/' .. 'daily',
    weeklies     = home .. '/' .. 'weekly',
    templates    = home .. '/' .. 'templates',

    -- image (sub)dir for pasting
    -- dir name (absolute path or subdir name)
    -- or nil if pasted images shouldn't go into a special subdir
    image_subdir = "img",

    -- markdown file extension
    extension    = ".md",

    -- Generate note filenames. One of:
    -- "title" (default) - Use title if supplied, uuid otherwise
    -- "uuid" - Use uuid
    -- "uuid-title" - Prefix title by uuid
    -- "title-uuid" - Suffix title with uuid
    new_note_filename = "title",
    -- file uuid type ("rand" or input for os.date()")
    uuid_type = "%Y%m%d%H%M",
    -- UUID separator
    uuid_sep = "-",

    -- following a link to a non-existing note will create it
    follow_creates_nonexisting = true,
    dailies_create_nonexisting = true,
    weeklies_create_nonexisting = true,

    -- skip telescope prompt for goto_today and goto_thisweek
    journal_auto_open = false,

    -- template for new notes (new_note, follow_link)
    -- set to `nil` or do not specify if you do not want a template
    template_new_note = home .. '/' .. 'templates/new_note.md',

    -- template for newly created daily notes (goto_today)
    -- set to `nil` or do not specify if you do not want a template
    template_new_daily = home .. '/' .. 'templates/daily.md',

    -- template for newly created weekly notes (goto_thisweek)
    -- set to `nil` or do not specify if you do not want a template
    template_new_weekly= home .. '/' .. 'templates/weekly.md',

    -- image link style
    -- wiki:     ![[image name]]
    -- markdown: ![](image_subdir/xxxxx.png)
    image_link_style = "markdown",

    -- default sort option: 'filename', 'modified'
    sort = "filename",

    -- integrate with calendar-vim
    plug_into_calendar = true,
    calendar_opts = {
        -- calendar week display mode: 1 .. 'WK01', 2 .. 'WK 1', 3 .. 'KW01', 4 .. 'KW 1', 5 .. '1'
        weeknm = 4,
        -- use monday as first day of week: 1 .. true, 0 .. false
        calendar_monday = 1,
        -- calendar mark: where to put mark for marked days: 'left', 'right', 'left-fit'
        calendar_mark = 'left-fit',
    },

    -- telescope actions behavior
    close_after_yanking = false,
    insert_after_inserting = true,

    -- tag notation: '#tag', ':tag:', 'yaml-bare'
    tag_notation = "#tag",

    -- command palette theme: dropdown (window) or ivy (bottom panel)
    command_palette_theme = "ivy",

    -- tag list theme:
    -- get_cursor: small tag list at cursor; ivy and dropdown like above
    show_tags_theme = "ivy",

    -- when linking to a note in subdir/, create a [[subdir/title]] link
    -- instead of a [[title only]] link
    subdirs_in_links = true,

    -- template_handling
    -- What to do when creating a new note via `new_note()` or `follow_link()`
    -- to a non-existing note
    -- - prefer_new_note: use `new_note` template
    -- - smart: if day or week is detected in title, use daily / weekly templates (default)
    -- - always_ask: always ask before creating a note
    template_handling = "smart",

    -- path handling:
    --   this applies to:
    --     - new_note()
    --     - new_templated_note()
    --     - follow_link() to non-existing note
    --
    --   it does NOT apply to:
    --     - goto_today()
    --     - goto_thisweek()
    --
    --   Valid options:
    --     - smart: put daily-looking notes in daily, weekly-looking ones in weekly,
    --              all other ones in home, except for notes/with/subdirs/in/title.
    --              (default)
    --
    --     - prefer_home: put all notes in home except for goto_today(), goto_thisweek()
    --                    except for notes with subdirs/in/title.
    --
    --     - same_as_current: put all new notes in the dir of the current note if
    --                        present or else in home
    --                        except for notes/with/subdirs/in/title.
    new_note_location = "smart",

    -- should all links be updated when a file is renamed
    rename_update_links = true,

    vaults = {
        vault2 = {
            -- alternate configuration for vault2 here. Missing values are defaulted to
            -- default values from telekasten.
            -- e.g.
            -- home = "/home/user/vaults/personal",
        },
    },

    -- how to preview media files
    -- "telescope-media-files" if you have telescope-media-files.nvim installed
    -- "catimg-previewer" if you have catimg installed
    media_previewer = "telescope-media-files",

    -- A customizable fallback handler for urls.
    follow_url_fallback = nil,
})
END
"""


