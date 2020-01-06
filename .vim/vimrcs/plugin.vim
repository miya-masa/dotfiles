" Enable plugin {{{
let s:plug_path = '~/.vim/autoload/plug.vim'
if has('nvim')
  let s:plug_path = '~/.local/share/nvim/site/autoload/plug.vim'
else
  let s:plug_path = '~/.vim/autoload/plug.vim'
endif

if !filereadable(glob(s:plug_path))
  call system('curl -fLo ' . s:plug_path . ' --create-dirs https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim')
  autocmd VimEnter * PlugInstall --sync | source ~/.config/nvim/init.vim
endif
" }}}
" VimPlug Start {{{
call plug#begin('~/.vim/plugged')
if !has('nvim')
  Plug 'roxma/vim-hug-neovim-rpc'
endif
Plug 'buoto/gotests-vim'
Plug 'AndrewRadev/splitjoin.vim'
Plug 'Shougo/vinarise.vim'
Plug 'SirVer/ultisnips'
Plug 'VincentCordobes/vim-translate'
Plug 'aklt/plantuml-syntax'
Plug 'alpaca-tc/html5.vim'
Plug 'bkad/CamelCaseMotion'
Plug 'c9s/perlomni.vim'
Plug 'cespare/vim-toml'
Plug 'christoomey/vim-tmux-navigator'
Plug 'davidhalter/jedi-vim'
Plug 'dhruvasagar/vim-table-mode'
Plug 'diepm/vim-rest-console'
Plug 'dracula/vim', { 'as': 'dracula' }
Plug 'ekalinin/Dockerfile.vim'
Plug 'elzr/vim-json'
Plug 'fatih/vim-go', { 'do': ':GoUpdateBinaries' }
Plug 'flazz/vim-colorschemes'
Plug 'fszymanski/fzf-gitignore', {'do': ':UpdateRemotePlugins'}
Plug 'tpope/vim-markdown'
Plug 'google/yapf', { 'rtp': 'plugins/vim', 'for': 'python' }
Plug 'honza/vim-snippets'
Plug 'itchyny/lightline.vim'
Plug 'cocopon/lightline-hybrid.vim'
Plug 'jiangmiao/auto-pairs'
Plug 'junegunn/fzf', { 'dir': '~/.fzf', 'do': './install --all' }
Plug 'junegunn/fzf.vim'
Plug 'junegunn/gv.vim'
Plug 'easymotion/vim-easymotion'
Plug 'junegunn/vim-easy-align'
Plug 'junegunn/vim-peekaboo'
Plug 'airblade/vim-rooter'
Plug 'iamcco/markdown-preview.nvim', { 'do': { -> mkdp#util#install() }}
Plug 'kylef/apiblueprint.vim'
Plug 'majutsushi/tagbar'
Plug 'mattn/emmet-vim'
Plug 'joshdick/onedark.vim'
Plug 'kristijanhusak/vim-hybrid-material'
Plug 'jonathanfilip/vim-lucius'
Plug 'maxmellon/vim-jsx-pretty'
Plug 'mhinz/vim-startify'
Plug 'mileszs/ack.vim'
Plug 'morhetz/gruvbox'
Plug 'shinchu/lightline-gruvbox.vim'
Plug 'tpope/vim-unimpaired'
Plug 'mxw/vim-jsx'
Plug 'nathanaelkane/vim-indent-guides'
Plug 'othree/es.next.syntax.vim'
Plug 'othree/html5.vim'
Plug 'othree/yajs.vim'
Plug 'pangloss/vim-javascript'
Plug 'ryanoasis/vim-devicons'
Plug 'sheerun/vim-polyglot'
Plug 'simeji/winresizer'
Plug 'sodapopcan/vim-twiggy'
Plug 'thinca/vim-qfreplace'
Plug 'thinca/vim-quickrun'
Plug 'thinca/vim-zenspace'
Plug 'tpope/vim-eunuch'
Plug 'tpope/vim-fugitive'
Plug 'tpope/vim-repeat'
Plug 'tpope/vim-rhubarb'
Plug 'tpope/vim-surround'
Plug 'vim-jp/vimdoc-ja'
Plug 'vim-scripts/DrawIt'
Plug 'w0rp/ale'
Plug 'xolox/vim-misc'
Plug 'xolox/vim-notes'
Plug 'tmux-plugins/vim-tmux-focus-events'
Plug 'tpope/vim-commentary'
Plug 'neoclide/coc.nvim', {'branch': 'release'}
Plug 'Shougo/neco-vim'
Plug 'editorconfig/editorconfig-vim'
Plug 'sjl/gundo.vim'
Plug 'itchyny/vim-gitbranch'
Plug 'scrooloose/nerdtree'
Plug 'Xuyuanp/nerdtree-git-plugin'
Plug 'stephpy/vim-yaml'

"
call plug#end()
" }}}
"Plugin Configuration {{{
"  neoclide/coc.nvim {{{
  function! SetupCommandAbbrs(from, to)
    exec 'cnoreabbrev <expr> '.a:from
          \ .' ((getcmdtype() ==# ":" && getcmdline() ==# "'.a:from.'")'
          \ .'? ("'.a:to.'") : ("'.a:from.'"))'
  endfunction

" Use C to open coc config
call SetupCommandAbbrs('C', 'CocConfig')
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
let g:vrc_trigger = '<Leader><C-j>'
" }}}
" CamelCaseMotion {{{
call camelcasemotion#CreateMotionMappings('<leader>')
" }}}
" vim-go {{{
let g:go_fmt_command = "goimports"
let g:go_fmt_autosave = 0
let g:go_autodetect_gopath = 1
let g:go_list_type = "quickfix"

" highlight
let g:go_highlight_types = 1
let g:go_highlight_fields = 1
let g:go_highlight_functions = 1
let g:go_highlight_methods = 1
let g:go_highlight_extra_types = 1
let g:go_highlight_generate_tags = 1

let g:go_test_timeout = "100s"
let g:go_metalinter_deadline = "30s"
let g:go_def_mode = 'godef'
let g:go_term_mode = 'vsplit'

" }}}
  " EmmetPlugin {{{
  let g:user_emmet_leader_key='<C-t>'
" }}}
" vim-json {{{
  let g:vim_json_syntax_conceal = 0
" }}}
" IndentGuide {{{
  let g:indent_guides_enable_on_vim_startup = 1
  let g:indent_guides_exclude_filetypes = ['help', 'startify', 'dirvish', 'no ft']
  let g:indent_guides_start_level = 1
  let g:indent_guides_guide_size = 1
  let g:indent_guides_default_mapping = 0
" }}}
" lightline {{{
"
  function! CocCurrentFunction()
      return get(b:, 'coc_current_function', '')
  endfunction

  let g:lightline = {
    \   'colorscheme': 'gruvbox',
    \   'active': {
    \     'left': [[ 'mode', 'paste' ],
    \               [ 'gitbranch', 'readonly', 'absolutepath', 'modified' ]],
    \     'right': [[ 'lineinfo' ],
    \                [ 'percent' ],
    \                [ 'cocstatus', 'currentfunction' ],
    \                [ 'fileformat', 'fileencoding', 'filetype', 'charvaluehex' ]]
    \   },
    \   'component': {
    \     'mode': '%{lightline#mode()}',
    \     'absolutepath': '%F',
    \     'relativepath': '%f',
    \     'filename': '%t',
    \     'modified': '%M',
    \     'bufnum': '%n',
    \     'paste': '%{&paste?"PASTE":""}',
    \     'readonly': '%R',
    \     'charvalue': '%b',
    \     'charvaluehex': '%B',
    \     'fileencoding': '%{&fenc!=#""?&fenc:&enc}',
    \     'fileformat': '%{&ff}',
    \     'filetype': '%{&ft!=#""?&ft:"no ft"}',
    \     'percent': '%3p%%',
    \     'percentwin': '%P',
    \     'spell': '%{&spell?&spelllang:""}',
    \     'lineinfo': '%3l:%-2v',
    \     'line': '%l',
    \     'column': '%c',
    \     'close': '%999X X ',
    \     'winnr': '%{winnr()}'
    \   },
    \   'component_function': {
    \       'gitbranch': 'gitbranch#name',
    \       'cocstatus': 'coc#status',
    \       'currentfunction': 'CocCurrentFunction'
    \   }
    \ }

" }}}
" tmux-navigator {{{
  nnoremap <silent> <BS> :TmuxNavigateLeft<cr>
" }}}
" ALE {{{
let g:ale_pattern_options = {
\   '\.go$': {
\       'ale_enabled': 0,
\   },
\   '\.md$': {
\       'ale_enabled': 0,
\   }
\}
" tmuxline {{{
let g:tmuxline_powerline_separators = 0
let g:tmuxline_preset = {
      \'a'    : '#S',
      \'b'    : '#(tmux-mem-cpu-load --colors)',
      \'c'    : ['#(whoami)'],
      \'win'  : ['#I', '#W'],
      \'cwin' : ['#I', '#W', '#F'],
      \'x'    : 'Online: #{online_status}',
      \'y'    : 'Batt: #{battery_icon} #{battery_percentage}',
      \'z'    : ['%R', '%a', '%Y'],
      \'options' : {'status-justify' : 'left'}}
" }}}
" vim-notes {{{
let g:notes_directories = ['~/work/Notes']
let g:notes_suffix = '.md'
" }}}
" Ack.vim {{{
  let g:ackprg = 'ag --nogroup --nocolor --column'
" }}}
" QuickRun {{{
let g:quickrun_config = {}
let g:quickrun_config.go = {'exec' : ['%c test']}
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
  let g:gotests_template_dir = $HOME . '/.config/nvim/gotests'
" }}}
" {{{ sjl/gundo
  let g:gundo_prefer_python3=1
" }}}
" {{{ Plug 'sheerun/vim-polyglot'
  let g:polyglot_disabled = ['go']
" }}}

" {{{ Plug 'scrooloose/nerdtree'
  let NERDTreeShowHidden=1
" }}}
