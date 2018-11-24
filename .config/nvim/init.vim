"               _                                             _
"    ____ ___  (_)_  ______ _      ____ ___  ____ __________ ( )_____
"   / __ `__ \/ / / / / __ `/_____/ __ `__ \/ __ `/ ___/ __ `/// ___/
"  / / / / / / / /_/ / /_/ /_____/ / / / / / /_/ (__  ) /_/ / (__  )
" /_/ /_/ /_/_/\__, /\__,_/     /_/ /_/ /_/\__,_/____/\__,_/ /____/
"             /____/
"     _       _ __        _
"    (_)___  (_) /__   __(_)___ ___
"   / / __ \/ / __/ | / / / __ `__ \
"  / / / / / / /__| |/ / / / / / / /
" /_/_/ /_/_/\__(_)___/_/_/ /_/ /_/
"
" Enable plugin {{{
filetype plugin indent on
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
  Plug 'roxma/nvim-yarp'
  Plug 'roxma/vim-hug-neovim-rpc'
endif
Plug 'SirVer/ultisnips'
Plug 'honza/vim-snippets'
Plug 'thinca/vim-qfreplace'
Plug 'thinca/vim-zenspace'
Plug 'tpope/vim-fugitive'
Plug 'justinmk/vim-dirvish'
Plug 'kristijanhusak/vim-dirvish-git'
Plug 'w0rp/ale'
Plug 'mattn/emmet-vim'
Plug 'alpaca-tc/html5.vim'
Plug 'othree/html5.vim'
Plug 'mxw/vim-jsx'
Plug 'miya-masa/vim-esformatter'
Plug 'elzr/vim-json'
Plug 'fatih/vim-go', { 'do': ':GoInstallBinaries' }
Plug 'AndrewRadev/splitjoin.vim'
Plug 'jodosha/vim-godebug'
" Plug 'Valloric/YouCompleteMe', { 'do': './install.py' }
if has('nvim')
  Plug 'Shougo/deoplete.nvim', { 'do': ':UpdateRemotePlugins' }
else
  Plug 'Shougo/deoplete.nvim'
  Plug 'roxma/nvim-yarp'
  Plug 'roxma/vim-hug-neovim-rpc'
endif
Plug 'zchee/deoplete-go', { 'do': 'make'}
Plug 'kylef/apiblueprint.vim'
Plug 'ekalinin/Dockerfile.vim'
Plug 'yaasita/edit-slack.vim'
Plug 'bkad/CamelCaseMotion'
Plug 'simeji/winresizer'
Plug 'godlygeek/tabular'
Plug 'plasticboy/vim-markdown'
Plug 'kannokanno/previm'
Plug 'vim-scripts/DrawIt'
Plug 'tomtom/tcomment_vim'
Plug 'tpope/vim-surround'
Plug 'bronson/vim-trailing-whitespace'
Plug 'nathanaelkane/vim-indent-guides'
Plug 'vim-jp/vimdoc-ja'
Plug 'aklt/plantuml-syntax'
Plug 'cespare/vim-toml'
Plug 'pangloss/vim-javascript'
Plug 'othree/yajs.vim'
Plug 'othree/es.next.syntax.vim'
Plug 'othree/javascript-libraries-syntax.vim'
Plug 'maxmellon/vim-jsx-pretty'
Plug 'ternjs/tern_for_vim'
Plug 'jiangmiao/auto-pairs'
Plug 'c9s/perlomni.vim'
Plug 'morhetz/gruvbox'
Plug 'junegunn/fzf', { 'dir': '~/.fzf', 'do': './install --all' }
Plug 'junegunn/fzf.vim'
Plug 'majutsushi/tagbar'
Plug 'dhruvasagar/vim-table-mode'
Plug 'thinca/vim-quickrun'
Plug 'diepm/vim-rest-console'
Plug 'VincentCordobes/vim-translate'
Plug 'junegunn/vim-easy-align'
Plug 'christoomey/vim-tmux-navigator'
Plug 'Konfekt/FastFold'
Plug 'itchyny/calendar.vim'
Plug 'xolox/vim-notes'
Plug 'xolox/vim-misc'
Plug 'tpope/vim-repeat'
Plug 'Shougo/vinarise.vim/'
Plug 'mileszs/ack.vim'
Plug 'tpope/vim-unimpaired'
Plug 'qpkorr/vim-bufkill'
Plug 'terryma/vim-multiple-cursors'
Plug 'davidhalter/jedi-vim'
Plug 'google/yapf', { 'rtp': 'plugins/vim', 'for': 'python' }
Plug 'Chiel92/vim-autoformat'
Plug 'scrooloose/vim-slumlord'
Plug 'jceb/vim-orgmode'
Plug 'mhinz/vim-startify'
" Plug 'edkolev/tmuxline.vim'

" Plugin Display {{{
Plug 'flazz/vim-colorschemes'
Plug 'ryanoasis/vim-devicons'
Plug 'airblade/vim-gitgutter'
Plug 'itchyny/lightline.vim'
Plug 'maximbaz/lightline-ale'
Plug 'dracula/vim', { 'as': 'dracula' }
" }}}
call plug#end()
" }}}
" Plugin Configuration {{{
" Plugin UltiSnips {{{
let g:UltiSnipsSnippetDirectories=["UltiSnips", "~/.config/nvim/UltiSnips", "UltiSnips_local"]
let g:UltiSnipsExpandTrigger="<C-l>"
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
" Go {{{
" vim-go
let g:go_fmt_command = "goimports"
" realize the autoformat plugin.
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

" lint
let g:go_metalinter_deadline = "30s"
let g:go_def_mode = 'godef'
let g:go_term_mode = 'vsplit'

" Guru Scope
" let g:go_guru_scope = []

augroup go
  autocmd!
  " Show by default 4 spaces for a tab
  autocmd BufNewFile,BufRead *.go setlocal noexpandtab tabstop=4 shiftwidth=4
  autocmd BufRead $GOPATH/src/*.go
        \  let s:tmp = matchlist(expand('%:p'),
        \  $GOPATH.'/src/\([^/]\+/[^/]\+/[^/]\+/\)')
        \| if len(s:tmp) > 1 |  exe 'silent :GoGuruScope ' . s:tmp[1] . '... -' . s:tmp[1] . 'vendor/...' | endif
        \| unlet s:tmp

  " :GoBuild and :GoTestCompile
  autocmd FileType go nmap <leader>gb :<C-u>call <SID>build_go_files()<CR>
  " :GoTest
  autocmd FileType go nmap <leader>gt  <Plug>(go-test)
  " :GoRun
  autocmd FileType go nmap <leader>gr  <Plug>(go-run)
  " :GoDoc
  autocmd FileType go nmap <Leader>gdoc <Plug>(go-doc)
  " :GoCoverageToggle
  autocmd FileType go nmap <Leader>gc <Plug>(go-coverage-toggle)
  " :GoInfo
  autocmd FileType go nmap <Leader>gi <Plug>(go-info)
  " :GoMetaLinter
  autocmd FileType go nmap <Leader>gl <Plug>(go-metalinter)
  " :GoDef but opens in a vertical split
  autocmd FileType go nmap <Leader>gv <Plug>(go-def-vertical)
  " :GoDef but opens in a horizontal split
  autocmd FileType go nmap <Leader>gs <Plug>(go-def-split)
  " :GoTestFunc
  autocmd FileType go nmap <Leader>gf <Plug>(go-test-func)

  " Open :GoDeclsDir with ctrl-g
  autocmd FileType go imap <C-g> <esc>:GoDecls<cr>
  autocmd FileType go nmap <C-g> :GoDeclsDir<cr>

  " :GoAlternate  commands :A, :AV, :AS and :AT
  autocmd Filetype go command! -bang A call go#alternate#Switch(<bang>0, 'edit')
  autocmd Filetype go command! -bang AV call go#alternate#Switch(<bang>0, 'vsplit')
  autocmd Filetype go command! -bang AS call go#alternate#Switch(<bang>0, 'split')
  autocmd Filetype go command! -bang AT call go#alternate#Switch(<bang>0, 'tabe')
  autocmd Filetype go command! GoRunArgs :!go run % <args>

  " GoKeyword
  autocmd FileType go set iskeyword=a-z,A-Z,48-57,&,*
augroup END
" build_go_files is a custom function that builds or compiles the test file.
" It calls :GoBuild if its a Go file, or :GoTestCompile if it's a test file
function! s:build_go_files()
  let l:file = expand('%')
  if l:file =~# '^\f\+_test\.go$'
    call go#test#Test(0, 1)
  elseif l:file =~# '^\f\+\.go$'
    call go#cmd#Build(0)
  endif
endfunction
" }}}
" EsFormatter {{{
augroup Vim-Esformatter
  autocmd!
  " for html
  autocmd FileType html,hbs noremap <buffer> <c-f> :call HtmlBeautify()<cr>
  " for css or scss
  autocmd FileType css noremap <buffer> <c-f> :call CSSBeautify()<cr>
  " My Bundles here:

  " will run esformatter after pressing <leader> followed by the 'e' and 's' keys
  autocmd FileType javascript noremap <silent>  <c-f> :Esformatter<CR>
  autocmd FileType javascript vnoremap <silent>  <c-f> :EsformatterVisual<CR>
augroup END
" }}}
" EmmetPlugin {{{
let g:user_emmet_leader_key='<C-t>'
" }}}
" vim-json {{{
let g:vim_json_syntax_conceal = 0
" }}}
" EditSlack {{{
if filereadable(expand('~/.vimrc.slack'))
  source ~/.vimrc.slack
  command! SlackPG :tabe slack://pg
  command! SlackCH :tabe slack://ch
  command! SlackDM :tabe slack://dm
  command! SlackME :tabe slack://dm/miyauchi.m
endif
" }}}
" Previm {{{
let g:previm_open_cmd = 'open -a Google\ Chrome'

augroup PrevimSettings
  autocmd!
  autocmd BufNewFile,BufRead *.{md,mdwn,mkd,mkdn,mark*} set filetype=markdown
augroup END
" }}}
" IndentGuide {{{
let g:indent_guides_enable_on_vim_startup = 1
" }}}
" PlantUML {{{
" augroup PlantUML
"   autocmd!
"   au FileType plantuml command! OpenUml :!open -a Google\ Chrome %
" augroup END
" }}}
" Javascript library syntax {{{
augroup JavascriptLibrariesSyntax
  autocmd!
  autocmd BufReadPre *.js let b:javascript_lib_use_underscore = 1
  autocmd BufReadPre *.js let b:javascript_lib_use_react = 1
augroup END
" }}}
" Align {{{
let g:Align_xstrlen=3
" }}}
" lightline {{{
let g:lightline = {
      \ 'colorscheme': 'gruvbox',
      \ 'active': {
      \   'left': [ [ 'mode', 'paste' ],
      \             [ 'gitbranch', 'readonly','absolutepath', 'modified' ]],
      \   'right': [ [ 'lineinfo' ],
      \              [ 'percent' ],
      \              [ 'fileformat', 'fileencoding', 'filetype', 'charvaluehex' ],
      \              [ 'linter_checking', 'linter_errors', 'linter_warnings', 'linter_ok' ]]
      \ },
      \ 'component': {
      \ 'mode': '%{lightline#mode()}',
      \ 'absolutepath': '%F',
      \ 'relativepath': '%f',
      \ 'filename': '%t',
      \ 'modified': '%M',
      \ 'bufnum': '%n',
      \ 'paste': '%{&paste?"PASTE":""}',
      \ 'readonly': '%R',
      \ 'charvalue': '%b',
      \ 'charvaluehex': '%B',
      \ 'fileencoding': '%{&fenc!=#""?&fenc:&enc}',
      \ 'fileformat': '%{&ff}',
      \ 'filetype': '%{&ft!=#""?&ft:"no ft"}',
      \ 'percent': '%3p%%',
      \ 'percentwin': '%P',
      \ 'spell': '%{&spell?&spelllang:""}',
      \ 'lineinfo': '%3l:%-2v',
      \ 'line': '%l',
      \ 'column': '%c',
      \ 'close': '%999X X ',
      \ 'winnr': '%{winnr()}'
      \ },
      \ 'component_function': {
      \   'gitbranch': 'fugitive#head'
      \ },
      \ }
let g:lightline.component_expand = {
      \  'linter_checking': 'lightline#ale#checking',
      \  'linter_warnings': 'lightline#ale#warnings',
      \  'linter_errors': 'lightline#ale#errors',
      \  'linter_ok': 'lightline#ale#ok',
      \ }
let g:lightline.component_type = {
      \     'linter_checking': 'left',
      \     'linter_warnings': 'warning',
      \     'linter_errors': 'error',
      \     'linter_ok': 'left',
      \ }
let g:lightline#ale#indicator_checking = "\uf110"
let g:lightline#ale#indicator_warnings = "\uf071"
let g:lightline#ale#indicator_errors = "\uf05e"
let g:lightline#ale#indicator_ok = "\uf00c"

" }}}
" tmux-navigator {{{
nnoremap <silent> <BS> :TmuxNavigateLeft<cr>
" }}}
" deoplete & deoplete-go {{{
let g:deoplete#enable_at_startup = 1
let g:deoplete#sources#go#gocode_binary = $GOPATH.'/bin/gocode'
let g:deoplete#sources#go#package_dot = 1
let g:deoplete#sources#go#sort_class = ['package', 'func', 'type', 'var', 'const']
" }}}
" FastFold {{{
let g:go_fold = 1
" }}}
" IndentGuide {{{
let g:indent_guides_start_level = 2
let g:indent_guides_guide_size = 1
" }}}
" ALE {{{
  " let g:ale_linters = {
  " \   'go': ['gometalinter'],
  " \}
  " let g:ale_go_gometalinter_options = '--vendored-linters --disable-all --enable=gotype --enable=vet --enable=golint -t'
  " let g:ale_go_gometalinter_options = '--fast'
  nnoremap <silent> [a <Plug>(ale_previous_wrap)
  nnoremap <silent> ]a <Plug>(ale_next_wrap)
" }}}
" calendar.vim {{{
let g:calendar_google_calendar = 1
" }}}
" fix-whitespace {{{
let g:extra_whitespace_ignored_filetypes = ['calendar']
" }}}
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
" YCM {{{
" }}}
" dirvish {{{
"
augroup dirvish
  autocmd!
  autocmd FileType dirvish command! -nargs=1 NF :e %<args>
augroup END
" }}}
" vim-unimpaired {{{
" }}}
" Ack.vim {{{
let g:ackprg = 'ag --nogroup --nocolor --column'
" }}}
" jedi/yapf {{{
augroup python
  autocmd!
  autocmd Filetype python map <C-F> :call yapf#YAPF()<cr>
  autocmd Filetype python imap <C-F> <c-o>:call yapf#YAPF()<cr>
augroup END
" }}}
" QuickRun {{{
  nnoremap <silent> <C-q> :QuickRun<CR>
" }}}
" Chiel92/vim-autoformat {{{
augroup autoformat
  autocmd!
  autocmd BufWrite *.go :Autoformat
  autocmd BufWrite *.json :Autoformat
augroup END
" }}}
" mhinz/vim-startify {{{
" startify
let g:startify_files_number = 5
let g:startify_list_order = [
        \ ['MRU'],
        \ 'files',
        \ ['MRUDir'],
        \ 'dir',
        \ ['Session'],
        \ 'sessions',
        \ ['Bookmarks'],
        \ 'bookmarks',
        \ ]
let g:startify_bookmarks = []

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
"
" }}}
" Basic Settings  {{{
scriptencoding utf8
set helplang=ja,en

set nowritebackup
set nobackup
set noswapfile
set noundofile
set noerrorbells
set novisualbell
set t_vb=
set tm=500
" viminfo
set viminfo='100,n$HOME/.vim/files/info/viminfo
" share clipboard
set clipboard+=unnamedplus
" disable 8 digits
set nrformats-=octal
set timeout timeoutlen=3000 ttimeoutlen=50
set hidden
set history=500
set formatoptions+=mM
set virtualedit=block
set whichwrap=b,s,[,],<,>
set backspace=indent,eol,start
set so=7
set ruler
set hid
set lazyredraw
" Use Unix as the standard file type
set ffs=unix,dos,mac
" Add a bit extra margin to the left
set foldcolumn=1
set ambiwidth=double
set inccommand=split
set wildmenu
if has('mouse')
  set mouse=a
endif
au FileType vim setlocal foldmethod=marker
set dictionary=/usr/share/dict/words
" }}}
" Search {{{
set ignorecase
set smartcase
set wrapscan
set incsearch
set hlsearch
set iskeyword=a-z,A-Z,48-57,_,.,-,>
" }}}
" Display {{{
set shellslash
set number
set showmatch matchtime=1
set ts=2 sw=2 sts=2
set autoindent
set smartindent
set wrap
set shiftwidth=2
set expandtab
set cinoptions+=:0
set title
set cmdheight=2
set laststatus=2
set showcmd
set display=lastline
set list
set listchars=tab:^\ ,trail:~
" }}}
" Spell Check {{{
set spelllang=en,cjk

fun! s:SpellConf()
  redir! => syntax
  silent syntax
  redir END

  set spell

  if syntax =~? '/<comment\>'
    syntax spell default
    syntax match SpellMaybeCode /\<\h\l*[_A-Z]\h\{-}\>/ contains=@NoSpell transparent containedin=Comment contained
  else
    syntax spell toplevel
    syntax match SpellMaybeCode /\<\h\l*[_A-Z]\h\{-}\>/ contains=@NoSpell transparent
  endif

  syntax cluster Spell add=SpellNotAscii,SpellMaybeCode
endfunc

augroup spell_check
  autocmd!
  autocmd BufReadPost,BufNewFile,Syntax * call s:SpellConf()
augroup END
" }}}
" Key map {{{
:let mapleader=","
" Opens a new tab with the current buffer's path
" Super useful when editing files in the same directory
map <leader>te :tabedit <c-r>=expand("%:p:h")<cr>/
" Close all the buffers
map <leader>bd :BD<cr>

" Switch CWD to the directory of the open buffer
map <leader>cd :cd %:p:h<cr>:pwd<cr>
" Useful mappings for managing tabs
map <leader>tn :tabnew<cr>
map <leader>to :tabonly<cr>
map <leader>tc :tabclose<cr>
map <leader>tm :tabmove<cr>
map <leader>t<leader> :tabnext<cr>
" Normal Mode {{{
nnoremap <F8> :source ~/.config/nvim/init.vim<CR>
nnoremap ZZ <Nop>
nnoremap <Down> gj
nnoremap <Up>   gk
nnoremap j gj
nnoremap k gk
nnoremap h <Left>zv
nnoremap l <Right>zv
nnoremap [q :cprevious<CR>
nnoremap ]q :cnext<CR>
nnoremap [Q :<C-u>cfirst<CR>
nnoremap ]Q :<C-u>clast<CR>
nnoremap Y y$
nnoremap <leader>a :cclose<CR>
nnoremap <leader>st :split<CR>:terminal<CR>
nnoremap <Leader><C-B> :Buffer<CR>
nnoremap <Leader><C-A> :Ag<CR>
nnoremap <Leader><C-G> :GFiles<CR>
nnoremap <Leader><C-F> :Files<CR>
nnoremap <leader><C-L> :Line<CR>
nnoremap <Leader><CR> :nohlsearch<CR>
nnoremap <Space><CR> V:!sh<CR>
nnoremap <Leader>gte V:TranslateVisual<CR>
nnoremap <Leader>gtj V:TranslateVisual ja:en<CR>
" }}}
" Termninal Mode {{{
tnoremap <silent> <leader><C-[> <C-\><C-n>
" }}}
" Visual Mode {{{
vnoremap <Space><CR> :!sh<CR>
vnoremap <Leader>gte :TranslateVisual<CR>
vnoremap <Leader>gtj :TranslateVisual ja:en<CR>
" Start interactive EasyAlign in visual mode (e.g. vip<Enter>)
vmap <Enter> <Plug>(EasyAlign)
" }}}
" }}}
" Colorscheme {{{
syntax enable
set background=dark
" set termguicolors
colorscheme gruvbox
" let g:airline_theme = 'gruvbox'
" }}}
" Util Command {{{
" Conv hex deg bin {{{
command! -nargs=1 ToH echo printf("%0x", <args>)
command! -nargs=1 ToD echo printf("%0d", <args>)
command! -nargs=1 ToB echo printf("%0b", <args>)
command! -nargs=1 ToHRegA let @a=printf("%0x", <args>)
command! -nargs=1 ToDRegA let @a=printf("%0d", <args>)
command! -nargs=1 ToBRegA let @a=printf("%0b", <args>)
" }}}
" }}}
"
