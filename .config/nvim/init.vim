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
  Plug 'roxma/vim-hug-neovim-rpc'
endif
Plug 'AndrewRadev/splitjoin.vim'
Plug 'Chiel92/vim-autoformat'
Plug 'Konfekt/FastFold'
Plug 'Shougo/vinarise.vim/'
Plug 'SirVer/ultisnips'
Plug 'VincentCordobes/vim-translate'
Plug 'airblade/vim-gitgutter'
Plug 'aklt/plantuml-syntax'
Plug 'alpaca-tc/html5.vim'
Plug 'bkad/CamelCaseMotion'
Plug 'bronson/vim-trailing-whitespace'
Plug 'c9s/perlomni.vim'
Plug 'cespare/vim-toml'
Plug 'jacoborus/tender.vim'
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
Plug 'godlygeek/tabular'
Plug 'google/yapf', { 'rtp': 'plugins/vim', 'for': 'python' }
Plug 'honza/vim-snippets'
Plug 'itchyny/calendar.vim'
Plug 'itchyny/lightline.vim'
Plug 'cocopon/lightline-hybrid.vim'
Plug 'jceb/vim-orgmode'
Plug 'jiangmiao/auto-pairs'
Plug 'jodosha/vim-godebug'
Plug 'junegunn/fzf', { 'dir': '~/.fzf', 'do': './install --all' }
Plug 'junegunn/fzf.vim'
Plug 'junegunn/gv.vim'
Plug 'junegunn/vim-easy-align'
Plug 'junegunn/vim-peekaboo'
Plug 'justinmk/vim-dirvish'
Plug 'iamcco/markdown-preview.nvim', { 'do': { -> mkdp#util#install() }}
Plug 'kristijanhusak/vim-dirvish-git'
Plug 'kylef/apiblueprint.vim'
Plug 'majutsushi/tagbar'
Plug 'mattn/emmet-vim'
Plug 'joshdick/onedark.vim'
Plug 'kristijanhusak/vim-hybrid-material'
Plug 'jonathanfilip/vim-lucius'
Plug 'maximbaz/lightline-ale'
Plug 'maxmellon/vim-jsx-pretty'
Plug 'mhinz/vim-startify'
Plug 'mileszs/ack.vim'
Plug 'miya-masa/vim-esformatter'
Plug 'morhetz/gruvbox'
Plug 'mxw/vim-jsx'
Plug 'nathanaelkane/vim-indent-guides'
Plug 'othree/es.next.syntax.vim'
Plug 'othree/html5.vim'
Plug 'othree/javascript-libraries-syntax.vim'
Plug 'othree/yajs.vim'
Plug 'pangloss/vim-javascript'
Plug 'plasticboy/vim-markdown'
Plug 'prabirshrestha/async.vim'
Plug 'prabirshrestha/vim-lsp'
Plug 'qpkorr/vim-bufkill'
Plug 'ryanoasis/vim-devicons'
Plug 'sheerun/vim-polyglot'
Plug 'simeji/winresizer'
Plug 'sodapopcan/vim-twiggy'
Plug 'ternjs/tern_for_vim'
Plug 'terryma/vim-multiple-cursors'
Plug 'thinca/vim-qfreplace'
Plug 'thinca/vim-quickrun'
Plug 'thinca/vim-zenspace'
Plug 'tpope/vim-eunuch'
Plug 'tpope/vim-fugitive'
Plug 'tpope/vim-repeat'
Plug 'tpope/vim-rhubarb'
Plug 'tpope/vim-sleuth'
Plug 'tpope/vim-surround'
Plug 'tpope/vim-unimpaired'
Plug 'vim-jp/vimdoc-ja'
Plug 'vim-scripts/DrawIt'
Plug 'w0rp/ale'
Plug 'xolox/vim-misc'
Plug 'xolox/vim-notes'
Plug 'yaasita/edit-slack.vim'
Plug 'tmux-plugins/vim-tmux-focus-events'
Plug 'tpope/vim-commentary'
Plug 'roxma/nvim-yarp'
Plug 'ncm2/ncm2'
Plug 'ncm2/ncm2-vim-lsp'
Plug 'ncm2/ncm2-bufword'
Plug 'ncm2/ncm2-path'
Plug 'ncm2/ncm2-tmux'
Plug 'ncm2/ncm2-ultisnips'
Plug 'ncm2/ncm2-vim'
Plug 'filipekiss/ncm2-look.vim'
Plug 'Shougo/neco-vim'
Plug 'editorconfig/editorconfig-vim'

"
call plug#end()
" }}}
" Plugin Configuration {{{
"  prabirshrestha/vim-lsp {{{
if executable('gopls')
    augroup gopls
    autocmd!
      au User lsp_setup call lsp#register_server({
          \ 'name': 'gopls',
          \ 'cmd': {server_info->['gopls', '-mode', 'stdio']},
          \ 'whitelist': ['go'],
          \ })
    augroup END
endif
if executable('docker-langserver')
    augroup docker-langserver
    autocmd!
      au User lsp_setup call lsp#register_server({
          \ 'name': 'docker-langserver',
          \ 'cmd': {server_info->['docker-langserver', '-stdio']},
          \ 'whitelist': ['Dockerfile'],
          \ })
    augroup END
endif
let g:lsp_diagnostics_enabled = 0
augroup vim-lsp
  autocmd!
  autocmd FileType go nmap <silent> <Leader>gi :LspHover<CR>
  autocmd FileType go nnoremap <silent> <Leader>gd :LspDefinition<CR>
  autocmd FileType go nnoremap <silent> <Leader>gn :LspDeclaration<CR>
augroup END
" }}}
" autozimu/LanguageClient-neovim {{{
    " let g:LanguageClient_rootMarkers = {
    "         \ 'go': ['.git', 'go.mod'],
    "         \ 'Dockerfile': ['.git'],
    "         \ }
    " let g:LanguageClient_serverCommands = {
    "     \ 'go': ['gopls', '-mode', 'stdio'],
    "     \ 'Dockerfile': ['docker-langserver', '--stdio'],
    "     \ }
    " let g:LanguageClient_diagnosticsEnable = 0
    " nnoremap <silent> <Leader>gi :call LanguageClient#textDocument_hover()<CR>
    " nnoremap <silent> <Leader>gd :call LanguageClient#textDocument_definition()<CR>
    " nnoremap <silent> <Leader>gn :call LanguageClient#textDocument_typeDefinition()<CR>
    " nnoremap <F5> :call LanguageClient_contextMenu()<CR>
"  }}}
"  ncm2/ncm2 {{{

  augroup ncm2
    autocmd!
    " enable ncm2 for all buffers
    autocmd BufEnter * call ncm2#enable_for_buffer()
    autocmd BufEnter * nnoremap <Leader>l :LookToggleBuffer<CR>
  augroup END
  " IMPORTANT: :help Ncm2PopupOpen for more information
  set completeopt=noinsert,menuone,noselect
  call ncm2#override_source('buflook', {'priority': 3})
  let g:ncm2_look_enabled = 1

"  }}}
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
let g:go_fmt_command = ""
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

let g:go_test_timeout = "100s"
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
  " :GoCoverageToggle
  autocmd FileType go nmap <Leader>gc <Plug>(go-coverage-toggle)
  " :GoMetaLinter
  autocmd FileType go nmap <Leader>gl <Plug>(go-metalinter)
  " :GoDef but opens in a vertical split
  autocmd FileType go nmap <Leader>gv <Plug>(go-def-vertical)
  " :GoDef but opens in a horizontal split
  autocmd FileType go nmap <Leader>gs <Plug>(go-def-split)
  " :GoTestFunc
  autocmd FileType go nmap <Leader>gf <Plug>(go-test-func)

  " :GoImports
  autocmd FileType go nnoremap <Leader><C-i> :GoImports<CR>

  autocmd FileType go nnoremap <Leader>fs :GoFillStruct<CR>
  autocmd FileType go nnoremap <Leader>ie :GoIfErr<CR>


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
" IndentGuide {{{
  let g:indent_guides_enable_on_vim_startup = 1
  let g:indent_guides_exclude_filetypes = ['help', 'startify', 'dirvish']
" }}}
" PlantUML {{{
augroup PlantUML
  autocmd!
  au FileType plantuml command! OpenUml :!open -a Google\ Chrome %
augroup END
" }}}
" Javascript library syntax {{{
augroup JavascriptLibrariesSyntax
  autocmd!
  autocmd BufReadPre *.js let b:javascript_lib_use_underscore = 1
  autocmd BufReadPre *.js let b:javascript_lib_use_react = 1
augroup END
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

  " Pass a dictionary to set multiple options
  " call deoplete#custom#option({
  " \ 'smart_case': v:true,
  " \ 'max_list': 500,
  " \ 'camel_case': v:true,
  " \ })
	" " Change the source rank
	" call deoplete#custom#source('dictionary', 'rank', 50)
" }}}
" FastFold {{{
  let g:go_fold_enabled=0
" }}}
" IndentGuide {{{
  let g:indent_guides_start_level = 2
  let g:indent_guides_guide_size = 1
" }}}
" ALE {{{
  let g:ale_linters = {
  \   'go': ['golangci-lint'],
  \}

  " let g:ale_go_gometalinter_options = '--vendored-linters --disable-all --enable=gotype --enable=vet --enable=golint -t'
  " let g:ale_go_golangci_lint_options = '--fast --disable=typecheck --enable=staticcheck --enable=gosimple --enable=unused'
  let g:ale_go_golangci_lint_options = '--fast --disable=typecheck --enable=staticcheck --enable=gosimple --enable=unused --tests=false'
  nmap <silent> [j <Plug>(ale_previous_wrap)
  nmap <silent> ]j <Plug>(ale_next_wrap)
" }}}
" calendar.vim {{{
let g:calendar_google_calendar = 1
" }}}
" fix-whitespace {{{
  let g:extra_whitespace_ignored_filetypes = ['calendar', 'startify']
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

  command! -nargs=0 Fq call fzf#run({
  \ 'source': 'ghq list --full-path',
  \ 'sink': 'Dirvish'
  \ })
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
  let g:quickrun_config = {}
  let g:quickrun_config.go = {'exec' : ['%c test']}
  nnoremap <silent> <C-q> :QuickRun -outputter message<CR>
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
" kannokanno/previm {{{
  let g:vim_markdown_folding_disabled = 1
" }}}
" VincentCordobes/vim-translate {{{
  let g:translate#default_languages = {
        \ 'en': 'ja',
        \ 'ja': 'en'
        \ }
" }}}
" {{{ junegunn/fzf.vim
  command! -nargs=0 Fq call fzf#run({
  \ 'source': 'ghq list --full-path',
  \ 'sink': 'Dirvish'
  \ })
" }}}
" {{{ scrooloose/nerdtree
  " map - :NERDTreeToggle %:p:h<cr>
  " command! -nargs=0 Fq call fzf#run({
  " \ 'source': 'ghq list --full-path',
  " \ 'sink': 'Dirvish'
  " \ })
  " let NERDTreeShowHidden=1
" }}}
"
" }}}
" Basic Settings  {{{
scriptencoding utf8
set helplang=ja,en

" Avoid garbled characters in Chinese language windows OS
let $LANG='ja_JP.UTF-8'
set langmenu=ja_JP.UTF-8
source $VIMRUNTIME/delmenu.vim
source $VIMRUNTIME/menu.vim

" Set 7 lines to the cursor - when moving vertically using j/k
set so=7

" Turn on the Wild menu
set wildmenu

" Ignore compiled files
set wildignore=*.o,*~,*.pyc
if has("win16") || has("win32")
    set wildignore+=.git\*,.hg\*,.svn\*
else
    set wildignore+=*/.git/*,*/.hg/*,*/.svn/*,*/.DS_Store
endif

" Height of the command bar
set cmdheight=2
" Ignore case when searching
set ignorecase
" When searching try to be smart about cases
set smartcase
" Highlight search results
set hlsearch
" Makes search act like search in modern browsers
set incsearch
set wrapscan
" Don't redraw while executing macros (good performance config)
set lazyredraw
" For regular expressions turn magic on
set magic
" Show matching brackets when text indicator is over them
set showmatch
" How many tenths of a second to blink when matching brackets
set mat=2
" No annoying sound on errors
set noerrorbells
set novisualbell
set t_vb=
set tm=500
" Use Unix as the standard file type
set ffs=unix,dos,mac
" Turn backup off, since most stuff is in SVN, git et.c anyway...
set nobackup
set nowb
set noswapfile
" Use spaces instead of tabs
set expandtab
" Be smart when using tabs ;)
set smarttab
set ai "Auto indent
set si "Smart indent
set wrap "Wrap lines
" viminfo
set viminfo='100,n$HOME/.vim/files/info/viminfo
" share clipboard
set clipboard+=unnamedplus
" disable 8 digits
set nrformats-=octal
set timeout timeoutlen=3000 ttimeoutlen=50
set hidden
set formatoptions+=mM
set virtualedit=block
set whichwrap=b,s,[,],<,>
set backspace=indent,eol,start
set ruler
set lazyredraw
set ambiwidth=double
set inccommand=split
set wildmenu
if has('mouse')
  set mouse=a
endif
au FileType vim setlocal foldmethod=marker
" Add a bit extra margin to the left
set foldcolumn=1
set dictionary=/usr/share/dict/words
set iskeyword=a-z,A-Z,48-57,_,.,-,>

" }}}
" Display {{{
"
set shellslash
set number
set showmatch matchtime=1
set ts=2 sw=2 sts=2
set cmdheight=2

" The value of this option influences when the last window will have a
" 	status line:
" 		2: always
set laststatus=2

" 	lastline	When included, as much as possible of the last line
" 			in a window will be displayed.  "@@@" is put in the
" 			last columns of the last screen line to indicate the
" 			rest of the line is not displayed.
set display=lastline

set list
set listchars=tab:^\ ,trail:~

" }}}
" Spell Check {{{
set spelllang=en,cjk
set spell

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

  syntax cluster Spell add=SpellMaybeCode
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
" Close the buffers
map <leader>bd :BD<cr>
" Close all the buffers
map <leader>ba :bufdo :BD<cr>

" Switch CWD to the directory of the open buffer
map <leader>cd :cd %:p:h<cr>:pwd<cr>

" Useful mappings for managing tabs
map <leader>tn :tabnew<cr>
map <leader>to :tabonly<cr>
map <leader>tc :tabclose<cr>
map <leader>tm :tabmove<cr>
map <leader>t<leader> :tabnext<cr>

" Quickly open a buffer for scribble
map <leader>q :e ~/buffer<cr>

" Quickly open a markdown buffer for scribble
map <leader>x :e ~/buffer.md<cr>

" Toggle paste mode on and off
map <leader>pp :setlocal paste!<cr>

" Normal Mode {{{
nnoremap <F8> :source ~/.config/nvim/init.vim<CR>
nnoremap ZZ <Nop>
nnoremap <Down> gj
nnoremap <Up>   gk
nnoremap j gj
nnoremap k gk
nnoremap h <Left>zv
nnoremap l <Right>zv
nnoremap Y y$
nnoremap <leader>a :cclose<CR>
nnoremap <leader>st :split<CR>:terminal<CR>
nnoremap <Leader><C-B> :Buffer<CR>
cnoreabbrev Ack Ack!
nnoremap <Leader><C-A> :Ack!<Space>
nnoremap <Leader><C-G> :GFiles<CR>
nnoremap <Leader><C-F> :Files<CR>
nnoremap <leader><C-L> :Line<CR>
nnoremap <leader><C-T> :Tags<CR>
nnoremap <leader><C-R> :Fq<CR>
nnoremap <Leader><CR> :nohlsearch<CR>
nnoremap <Space><CR> V:!sh<CR>
nnoremap <Leader>tve V:TranslateVisual<CR>
nnoremap <Leader>tvj V:TranslateVisual ja:en<CR>
" }}}
" Termninal Mode {{{
tnoremap <silent> <leader><C-[> <C-\><C-n>

" Insert Mode {{{

" }}}
" }}}
" Visual Mode {{{
vnoremap <Space><CR> :!sh<CR>
vnoremap <Leader>tve :TranslateVisual<CR>
vnoremap <Leader>tvj :TranslateVisual ja:en<CR>
" Start interactive EasyAlign in visual mode (e.g. vip<Enter>)
vmap <Enter> <Plug>(EasyAlign)

" }}}
" }}}
" Colorscheme {{{
" Enable syntax highlighting
syntax enable

" Enable 256 colors palette in Gnome Terminal
if $COLORTERM == 'gnome-terminal'
    set t_Co=256
endif

try
  colorscheme gruvbox
catch
endtry
set background=dark

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
