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
Plug 'Shougo/vinarise.vim'
Plug 'SirVer/ultisnips'
Plug 'VincentCordobes/vim-translate'
Plug 'airblade/vim-rooter'
Plug 'aklt/plantuml-syntax'
Plug 'bkad/CamelCaseMotion'
Plug 'bronson/vim-trailing-whitespace'
Plug 'christoomey/vim-tmux-navigator'
Plug 'rhysd/vim-go-impl'
" Plug 'cocopon/lightline-hybrid.vim'
Plug 'dhruvasagar/vim-table-mode'
Plug 'diepm/vim-rest-console'
Plug 'easymotion/vim-easymotion'
Plug 'edkolev/tmuxline.vim'
Plug 'flazz/vim-colorschemes'
Plug 'honza/vim-snippets'
Plug 'iamcco/markdown-preview.nvim', { 'do': 'cd app && yarn install'  }
" Plug 'itchyny/lightline.vim'
" Plug 'itchyny/vim-gitbranch'
Plug 'windwp/nvim-autopairs'
Plug 'junegunn/fzf', { 'dir': '~/.fzf', 'do': './install --all' }
Plug 'junegunn/fzf.vim'
Plug 'junegunn/goyo.vim'
Plug 'junegunn/gv.vim'
Plug 'junegunn/vim-easy-align'
Plug 'kana/vim-operator-replace'
Plug 'kana/vim-operator-user'
" Plug 'majutsushi/tagbar'
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
Plug 'tpope/vim-commentary'
Plug 'tpope/vim-dispatch'
Plug 'tpope/vim-fugitive'
Plug 'tpope/vim-markdown'
Plug 'tpope/vim-projectionist'
Plug 'tpope/vim-repeat'
Plug 'tpope/vim-surround'
Plug 'tpope/vim-unimpaired'
Plug 'tpope/vim-obsession'
Plug 'vim-jp/vimdoc-ja'
Plug 'vim-scripts/DrawIt'
Plug 'vim-test/vim-test'
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
Plug 'quangnguyen30192/cmp-nvim-ultisnips'
Plug 'uga-rosa/cmp-dictionary'
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
local null_ls = require("null-ls")

-- register any number of sources simultaneously
local sources = {
    null_ls.builtins.formatting.prettier,
    null_ls.builtins.formatting.stylua,
    null_ls.builtins.diagnostics.write_good,
    null_ls.builtins.diagnostics.eslint,
}

null_ls.setup({ sources = sources })
EOF


lua << EOF
require('nvim-autopairs').setup{}
local tree_cb = require'nvim-tree.config'.nvim_tree_callback
-- default mappings
local list = {
  { key = {"<CR>", "o", "<2-LeftMouse>"}, cb = tree_cb("edit") },
  { key = {"<2-RightMouse>", "<C-]>"},    cb = tree_cb("cd") },
  { key = "<C-v>",                        cb = tree_cb("vsplit") },
  { key = "<C-x>",                        cb = tree_cb("split") },
  { key = "<C-t>",                        cb = tree_cb("tabnew") },
  { key = "<",                            cb = tree_cb("prev_sibling") },
  { key = ">",                            cb = tree_cb("next_sibling") },
  { key = "P",                            cb = tree_cb("parent_node") },
  { key = "<S-CR>",                       cb = tree_cb("close_node") },
  { key = "<Tab>",                        cb = tree_cb("preview") },
  { key = "K",                            cb = tree_cb("first_sibling") },
  { key = "J",                            cb = tree_cb("last_sibling") },
  { key = "I",                            cb = tree_cb("toggle_ignored") },
  { key = "H",                            cb = tree_cb("toggle_dotfiles") },
  { key = "R",                            cb = tree_cb("refresh") },
  { key = "a",                            cb = tree_cb("create") },
  { key = "d",                            cb = tree_cb("remove") },
  { key = "r",                            cb = tree_cb("rename") },
  { key = "<C-r>",                        cb = tree_cb("full_rename") },
  { key = "x",                            cb = tree_cb("cut") },
  { key = "yy",                           cb = tree_cb("copy") },
  { key = "p",                            cb = tree_cb("paste") },
  { key = "cp",                           cb = tree_cb("copy_name") },
  { key = "Y",                            cb = tree_cb("copy_path") },
  { key = "gy",                           cb = tree_cb("copy_absolute_path") },
  { key = "[c",                           cb = tree_cb("prev_git_item") },
  { key = "]c",                           cb = tree_cb("next_git_item") },
  { key = "<BS>",                         cb = tree_cb("dir_up") },
  { key = "q",                            cb = tree_cb("close") },
  { key = "?",                            cb = tree_cb("toggle_help") },
}

require'nvim-tree'.setup {
  view = {
    mappings = {
      custom_only = false,
      list = list
    },
  },
}

local nvim_lsp = require('lspconfig')

-- Use an on_attach function to only map the following keys
-- after the language server attaches to the current buffer
local on_attach = function(client, bufnr)
  local function buf_set_keymap(...) vim.api.nvim_buf_set_keymap(bufnr, ...) end
  local function buf_set_option(...) vim.api.nvim_buf_set_option(bufnr, ...) end
  client.resolved_capabilities.document_formatting = false

  -- Enable completion triggered by <c-x><c-o>
  buf_set_option('omnifunc', 'v:lua.vim.lsp.omnifunc')

  -- Mappings.
  local opts = { noremap=true, silent=true }

  -- See `:help vim.lsp.*` for documentation on any of the below functions
  buf_set_keymap('n', '<Leader>gD', '<cmd>lua vim.lsp.buf.declaration()<CR>', opts)
  buf_set_keymap('n', '<Leader>gd', '<cmd>lua vim.lsp.buf.definition()<CR>', opts)
  buf_set_keymap('n', 'K', '<cmd>lua vim.lsp.buf.hover()<CR>', opts)
  buf_set_keymap('n', '<Leader>gi', '<cmd>lua vim.lsp.buf.implementation()<CR>', opts)
  buf_set_keymap('n', '<Leader><C-k>', '<cmd>lua vim.lsp.buf.signature_help()<CR>', opts)
  buf_set_keymap('n', '<space>wa', '<cmd>lua vim.lsp.buf.add_workspace_folder()<CR>', opts)
  buf_set_keymap('n', '<space>wr', '<cmd>lua vim.lsp.buf.remove_workspace_folder()<CR>', opts)
  buf_set_keymap('n', '<space>wl', '<cmd>lua print(vim.inspect(vim.lsp.buf.list_workspace_folders()))<CR>', opts)
  buf_set_keymap('n', '<Leader>D', '<cmd>lua vim.lsp.buf.type_definition()<CR>', opts)
  buf_set_keymap('n', '<Leader>rn', '<cmd>lua vim.lsp.buf.rename()<CR>', opts)
  buf_set_keymap('n', '<Leader>ca', '<cmd>lua vim.lsp.buf.code_action()<CR>', opts)
  buf_set_keymap('n', '<Leader>gr', '<cmd>lua vim.lsp.buf.references()<CR>', opts)
  buf_set_keymap('n', '<space>e', '<cmd>lua vim.diagnostic.show_line_diagnostics()<CR>', opts)
  buf_set_keymap('n', '[g', '<cmd>lua vim.diagnostic.goto_prev()<CR>', opts)
  buf_set_keymap('n', ']g', '<cmd>lua vim.diagnostic.goto_next()<CR>', opts)
  buf_set_keymap('n', '<space>q', '<cmd>lua vim.diagnostic.set_loclist()<CR>', opts)
  buf_set_keymap('n', '<Leader><C-f>', '<cmd>lua vim.lsp.buf.formatting()<CR>', opts)
end

-- Use a loop to conveniently call 'setup' on multiple servers and
-- map buffer local keybindings when the language server attaches
  -- Setup nvim-cmp.
  local cmp = require'cmp'

  cmp.setup({
    snippet = {
      -- REQUIRED - you must specify a snippet engine
      expand = function(args)
        -- vim.fn["vsnip#anonymous"](args.body) -- For `vsnip` users.
        -- require('luasnip').lsp_expand(args.body) -- For `luasnip` users.
        vim.fn["UltiSnips#Anon"](args.body) -- For `ultisnips` users.
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
    },
    sources = cmp.config.sources({
      { name = 'nvim_lsp' },
      { name = 'ultisnips'}, -- For ultisnips users.
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
local capabilities = require('cmp_nvim_lsp').update_capabilities(vim.lsp.protocol.make_client_capabilities())
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
            completeUnimported = true,
            gofumpt = true,
            experimentalPostfixCompletions = true
          }
        }
    end
    opts.on_attach = on_attach
    opts.capabilities = capabilities

    -- This setup() function is exactly the same as lspconfig's setup function.
    -- Refer to https://github.com/neovim/nvim-lspconfig/blob/master/ADVANCED_README.md
    server:setup(opts)
end)
require'lspconfig'.golangci_lint_ls.setup{}
EOF

lua <<EOF
require'nvim-treesitter.configs'.setup {
  textobjects = {
    select = {
      enable = true,

      -- Automatically jump forward to textobj, similar to targets.vim
      lookahead = true,

      keymaps = {
        -- You can use the capture groups defined in textobjects.scm
        ["af"] = "@function.outer",
        ["if"] = "@function.inner",
        ["ac"] = "@class.outer",
        ["ic"] = "@class.inner"
      },
    },
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
" script_31337_path_and_na[m]e_without_extension_11
" }}}
" vim-go {{{
" let g:go_gopls_enabled = 0
" let g:go_fmt_command = "goimports"
" let g:go_fmt_autosave = 0
" let g:go_mod_fmt_autosave = 0
" let g:go_autodetect_gopath = 0
" let g:go_list_type = "quickfix"
" let g:go_doc_keywordprg_enabled = 0
" let g:go_def_mapping_enabled = 0
" let g:go_template_autocreate = 0
" let g:go_echo_go_info = 0
" let g:go_echo_command_info = 1

" " highlight
" let g:go_highlight_types = 0
" let g:go_highlight_fields = 0
" let g:go_highlight_functions = 0
" let g:go_highlight_methods = 0
" let g:go_highlight_extra_types = 0
" let g:go_highlight_generate_tags = 0
" let g:go_auto_sameids = 0

" let g:go_test_timeout = "100s"
" let g:go_metalinter_deadline = "30s"
" let g:go_def_mode = 'godef'
" let g:go_term_mode = 'vsplit'

" }}}
" EmmetPlugin {{{
let g:user_emmet_leader_key='<C-t>'
" }}}
" vim-json {{{
let g:vim_json_syntax_conceal = 0
" }}}
" IndentGuide {{{
" let g:indent_guides_enable_on_vim_startup = 1
" let g:indent_guides_exclude_filetypes = ['help', 'startify', 'dirvish', 'no ft', 'fzf', 'nerdtree', 'defx']
" let g:indent_guides_start_level = 1
" let g:indent_guides_guide_size = 1
" let g:indent_guides_default_mapping = 0
" }}}
" lightline {{{
lua << END
require'lualine'.setup {
  options = {
    theme = 'gruvbox-material'
  }
}
END
"
" let g:lightline = {
"       \   'colorscheme': 'gruvbox',
"       \   'active': {
"       \     'left': [[ 'mode', 'paste' ],
"       \               [ 'gitbranch', 'readonly', 'absolutepath', 'modified' ]],
"       \     'right': [[ 'lineinfo' ],
"       \                [ 'percent' ],
"       \                [ 'fileformat', 'fileencoding', 'filetype', 'charvaluehex' ]]
"       \   },
"       \   'component': {
"       \     'mode': '%{lightline#mode()}',
"       \     'absolutepath': '%F',
"       \     'relativepath': '%f',
"       \     'filename': '%t',
"       \     'modified': '%M',
"       \     'bufnum': '%n',
"       \     'paste': '%{&paste?"PASTE":""}',
"       \     'readonly': '%R',
"       \     'charvalue': '%b',
"       \     'charvaluehex': '%B',
"       \     'fileencoding': '%{&fenc!=#""?&fenc:&enc}',
"       \     'fileformat': '%{&ff}',
"       \     'filetype': '%{&ft!=#""?&ft:"no ft"}',
"       \     'percent': '%3p%%',
"       \     'percentwin': '%P',
"       \     'spell': '%{&spell?&spelllang:""}',
"       \     'lineinfo': '%3l:%-2v',
"       \     'line': '%l',
"       \     'column': '%c',
"       \     'close': '%999X X ',
"       \     'winnr': '%{winnr()}'
"       \   },
"       \   'component_function': {
"       \       'gitbranch': 'gitbranch#name'
"       \   }
"       \ }

" }}}
" tmux-navigator {{{
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
" let g:gotests_template_dir = $HOME . '/go/src/github.com/cweill/gotests/templates/testify'
" }}}
" {{{ sjl/gundo
let g:gundo_prefer_python3=1
" }}}
" {{{ Plug 'scrooloose/nerdtree'
let NERDTreeShowHidden=1
let g:NERDTreeMapJumpPrevSibling=""
let g:NERDTreeMapJumpNextSibling=""
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
      \ }}
" }}}
" Plug 'Plug 'tpope/vim-dispatch'' {{{
let g:dispatch_compilers = {'go test': 'gotest'}
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
"  Plug junegunn/fzf'' {{{
command! -bang -nargs=* GGrep
      \ call fzf#vim#grep(
      \   'git grep --line-number '.shellescape(<q-args>), 0,
      \   fzf#vim#with_preview({'dir': systemlist('git rev-parse --show-toplevel')[0]}), <bang>0)
" }}}
" Plug 'airblade/vim-rooter' {{{
let g:rooter_manual_only = 1
" }}}
" Plug 'tpope/vim-markdown' {{{
let g:markdown_fenced_languages = ['plantuml', 'go', 'java', 'bash=sh']
" }}}
" Plug 'Yggdroot/indentLine' {{{
" let g:indentLine_fileTypeExclude = ['help', 'startify', 'dirvish', 'no ft', 'fzf', 'nerdtree', 'defx', 'go']

lua << EOF
require("indent_blankline").setup {
    char = "|",
    filetype_exclude = {"help", "startify", "dirvish", "no ft", "fzf", 'NvimTree', 'markdown'}
}
EOF
" }}}
command! -bang -nargs=* Rg
  \ call fzf#vim#grep(
  \   'rg --column --line-number --no-heading --color=always --hidden --iglob ''!.git'' --smart-case -- '.shellescape(<q-args>), 1,
  \   fzf#vim#with_preview(), <bang>0)

" }}}
"
" Plug 'iamcco/markdown-preview.nvim'
let g:mkdp_open_to_the_world = 1
let g:mkdp_port = '39999'
let g:mkdp_echo_preview_url = 1
let g:mkdp_preview_options = {
      \ 'uml': {
      \  'server': 'http://plantuml-server.internal:8989'
      \ },
    \ }
" }}}
"
