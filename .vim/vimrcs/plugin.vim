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
" Plug 'dracula/vim', { 'as': 'dracula' }
" Plug 'jonathanfilip/vim-lucius'
" Plug 'joshdick/onedark.vim'
" Plug 'kristijanhusak/vim-hybrid-material'
" Plug 'morhetz/gruvbox'
" Plug 'w0rp/ale'
Plug 'AndrewRadev/splitjoin.vim'
Plug 'Chiel92/vim-autoformat'
Plug 'Shougo/vinarise.vim'
Plug 'SirVer/ultisnips'
Plug 'VincentCordobes/vim-translate'
Plug 'Xuyuanp/nerdtree-git-plugin'
Plug 'airblade/vim-rooter'
Plug 'aklt/plantuml-syntax'
Plug 'antoinemadec/coc-fzf'
Plug 'bkad/CamelCaseMotion'
Plug 'bronson/vim-trailing-whitespace'
Plug 'cespare/vim-toml'
Plug 'christoomey/vim-tmux-navigator'
Plug 'cocopon/lightline-hybrid.vim'
Plug 'dhruvasagar/vim-table-mode'
Plug 'diepm/vim-rest-console'
Plug 'easymotion/vim-easymotion'
Plug 'edkolev/tmuxline.vim'
Plug 'ekalinin/Dockerfile.vim'
Plug 'elzr/vim-json'
Plug 'flazz/vim-colorschemes'
Plug 'google/yapf', { 'rtp': 'plugins/vim', 'for': 'python' }
Plug 'honza/vim-snippets'
Plug 'iamcco/markdown-preview.nvim', { 'do': { -> mkdp#util#install() }}
Plug 'itchyny/lightline.vim'
Plug 'itchyny/vim-gitbranch'
Plug 'jiangmiao/auto-pairs'
Plug 'junegunn/fzf', { 'dir': '~/.fzf', 'do': './install --all' }
Plug 'junegunn/fzf.vim'
Plug 'junegunn/goyo.vim'
Plug 'junegunn/gv.vim'
Plug 'junegunn/vim-easy-align'
Plug 'junegunn/vim-peekaboo'
Plug 'kana/vim-operator-replace'
Plug 'kana/vim-operator-user'
Plug 'kylef/apiblueprint.vim'
Plug 'majutsushi/tagbar'
Plug 'mattn/emmet-vim'
Plug 'maxmellon/vim-jsx-pretty'
Plug 'mhinz/vim-startify'
Plug 'miya-masa/fillstruct-vim'
Plug 'miya-masa/gotest-compiler-vim'
Plug 'mxw/vim-jsx'
Plug 'nathanaelkane/vim-indent-guides'
Plug 'neoclide/coc.nvim', {'branch': 'release'}
Plug 'raghur/vim-ghost', {'do': ':GhostInstall'}
Plug 'ryanoasis/vim-devicons'
Plug 'scrooloose/nerdtree'
Plug 'sebdah/vim-delve'
Plug 'shinchu/lightline-gruvbox.vim'
Plug 'simeji/winresizer'
Plug 'sjl/gundo.vim'
Plug 'stefandtw/quickfix-reflector.vim'
Plug 'stephpy/vim-yaml'
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
Plug 'vim-jp/vimdoc-ja'
Plug 'vim-scripts/DrawIt'
Plug 'vim-test/vim-test'
Plug 'xolox/vim-misc'
Plug 'xolox/vim-notes'

call plug#end()
" }}}
"  neoclide/coc.nvim {{{
inoremap <silent><expr> <c-0> coc#refresh()
let g:coc_global_extensions = ['coc-dictionary', 'coc-emmet', 'coc-git', 'coc-go', 'coc-java', 'coc-json', 'coc-lists', 'coc-python', 'coc-snippets', 'coc-sql', 'coc-word', 'coc-yaml', 'coc-sh']
" Add `:Format` command to format current buffer.
command! -nargs=0 Format :call CocAction('format')

" Add `:OR` command for organize imports of the current buffer.
command! -nargs=0 OR :call CocAction('runCommand', 'editor.action.organizeImport')
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
let g:indent_guides_enable_on_vim_startup = 1
let g:indent_guides_exclude_filetypes = ['help', 'startify', 'dirvish', 'no ft', 'fzf', 'nerdtree']
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
" let g:ale_pattern_options = {
"       \   '\.go$': {
"       \       'ale_enabled': 0,
"       \   },
"       \   '\.md$': {
"       \       'ale_enabled': 0,
"       \   }
"       \}
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
" {{{ Plug 'scrooloose/nerdtree'
let NERDTreeShowHidden=1
" }}}
" {{{ Plug 'janko/vim-test'
let test#strategy = "dispatch"
let test#go#gotest#options = {
  \ 'nearest': '-count=1',
  \ 'file':    '-count=1',
  \ 'suite':   '-count=1',
\}
" }}}
"  Plug 'kana/vim-operator-replace' {{{
map ! <Plug>(operator-replace)
" }}}
"  Plug 'tpop/projectionist' {{{
let g:projectionist_heuristics = {
      \ "go.mod": {
      \   "*_test.go": {"type": "test", "alternate": "{}.go"},
      \   "*.go": {"type": "source", "alternate": "{}_test.go"}
      \ }}
" }}}
" Plug 'Plug 'tpope/vim-dispatch'' {{{
let g:dispatch_compilers = {'go test': 'gotest'}
" }}}
" Plug 'antoinemadec/coc-fzf' {{{
nnoremap <silent> <leader><space>c  :<C-u>CocFzfList commands<CR>
nnoremap <silent> <leader><space>e  :<C-u>CocFzfList extensions<CR>
nnoremap <silent> <leader><space>l  :<C-u>CocFzfList location<CR>
nnoremap <silent> <leader><space>o  :<C-u>CocFzfList outline<CR>
nnoremap <silent> <leader><space>s  :<C-u>CocFzfList symbols<CR>
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
" Plug 'tpope/vim-markdown'
let g:markdown_fenced_languages = ['plantuml', 'go', 'java', 'bash=sh']
" }}}
