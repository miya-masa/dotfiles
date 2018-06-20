scriptencoding utf8
set helplang=ja,en
" ファイルの上書きの前にバックアップを作る/作らない
" set writebackupを指定してもオプション 'backup' がオンでない限り、
" バックアップは上書きに成功した後に削除される。
set nowritebackup
" バックアップ/スワップファイルを作成する/しない
set nobackup
set noswapfile
set noundofile
" viminfoを作成しない
set viminfo=
" クリップボードを共有
set clipboard+=unnamedplus
" 8進数を無効にする。<C-a>,<C-x>に影響する
set nrformats-=octal
" キーコードやマッピングされたキー列が完了するのを待つ時間(ミリ秒)
set timeout timeoutlen=3000 ttimeoutlen=50
" 編集結果非保存のバッファから、新しいバッファを開くときに警告を出さない
set hidden
" ヒストリの保存数
set history=500
" 日本語の行の連結時には空白を入力しない
set formatoptions+=mM
" Visual blockモードでフリーカーソルを有効にする
set virtualedit=block
" カーソルキーで行末／行頭の移動可能に設定
set whichwrap=b,s,[,],<,>
" バックスペースでインデントや改行を削除できるようにする
set backspace=indent,eol,start
" □や○の文字があってもカーソル位置がずれないようにする
set ambiwidth=double
" コマンドライン補完するときに強化されたものを使う
set wildmenu
" マウスを有効にする
if has('mouse')
  set mouse=a
endif
" pluginを使用可能にする
filetype plugin indent on

"----------------------------------------
" 検索
"----------------------------------------
" 検索の時に大文字小文字を区別しない
" ただし大文字小文字の両方が含まれている場合は大文字小文字を区別する
set ignorecase
set smartcase
" 検索時にファイルの最後まで行ったら最初に戻る
set wrapscan
" インクリメンタルサーチ
set incsearch
" 検索文字の強調表示
set hlsearch
" w,bの移動で認識する文字
" set iskeyword=a-z,A-Z,48-57,_,.,-,>
" vimgrep をデフォルトのgrepとする場合internal
" set grepprg=internal

"----------------------------------------
" 表示設定
"----------------------------------------
" スプラッシュ(起動時のメッセージ)を表示しない
" set shortmess+=I
" エラー時の音とビジュアルベルの抑制(gvimは.gvimrcで設定)
set noerrorbells
set novisualbell
set visualbell t_vb=
" マクロ実行中などの画面再描画を行わない
" WindowsXpまたはWindowテーマが「Windowsクラシック」で
" Google日本語入力を使用するとIビームカーソルが残る場合にも有効
" set lazyredraw
" Windowsでディレクトリパスの区切り文字表示に / を使えるようにする
set shellslash
" 行番号表示
set number
" 括弧の対応表示時間
set showmatch matchtime=1
" タブを設定
" set ts=2 sw=2 sts=2
set tabstop=2
" 自動的にインデントする
set autoindent
set shiftwidth=2
set expandtab
" Cインデントの設定
set cinoptions+=:0
" タイトルを表示
set title
" コマンドラインの高さ (gvimはgvimrcで指定)
set cmdheight=2
set laststatus=2
" コマンドをステータス行に表示
set showcmd
" 画面最後の行をできる限り表示する
set display=lastline
" Tab、行末の半角スペースを明示的に表示する
set list
set listchars=tab:^\ ,trail:~

"----------------------------------------
" ノーマルモード
"----------------------------------------
" leaderの設定
:let mapleader=","
" 現在開いているvimスクリプトファイルを実行
nnoremap <F8> :source %<CR>
" 強制全保存終了を無効化
nnoremap ZZ <Nop>
" カーソルをj k では表示行で移動する。物理行移動は<C-n>,<C-p>
" キーボードマクロには物理行移動を推奨
" h l は行末、行頭を超えることが可能に設定(whichwrap)
nnoremap <Down> gj
nnoremap <Up>   gk
nnoremap j gj
nnoremap k gk
nnoremap h <Left>zv
nnoremap l <Right>zv
nnoremap Y y$
nnoremap H ^
nnoremap L $
vnoremap L g_
nnoremap <C-j> <C-W>j
nnoremap <C-k> <C-W>k
nnoremap <C-h> <C-W>h
nnoremap <C-l> <C-W>l
nnoremap <C-[><C-[> :nohlsearch<CR>

" Some useful quickfix shortcuts for quickfix
nnoremap <C-n> :cn<CR>
nnoremap <C-m> :cp<CR>
nnoremap <leader>a :cclose<CR>

" vimshell
tnoremap <silent> <leader><C-[> <C-\><C-n>
nnoremap <leader>vt :tabnew<CR>:terminal<CR>
nnoremap <leader>st :split<CR>:terminal<CR>
map <C-[> <ESC>

""""""""""""""""""""""""""""""
" 全角スペースを表示
""""""""""""""""""""""""""""""
" コメント以外で全角スペースを指定しているので、scriptencodingと、
" このファイルのエンコードが一致するよう注意！
" 強調表示されない場合、ここでscriptencodingを指定するとうまくいく事があります。
" scriptencoding cp932
"
function! s:GetHighlight(hi)
  redir => hl
  exec 'highlight '.a:hi
  redir END
  let hl = substitute(hl, '[\r\n]', '', 'g')
  let hl = substitute(hl, 'xxx', '', '')
  return hl
endfunction
function! ZenkakuSpace()
  silent! let hi = s:GetHighlight('ZenkakuSpace')
  if hi =~ 'E411' || hi =~ 'cleared$'
    highlight ZenkakuSpace cterm=underline ctermfg=darkgrey gui=underline guifg=darkgrey
  endif
endfunction
if has('syntax')
  augroup ZenkakuSpace
    autocmd!
    autocmd ColorScheme       * call ZenkakuSpace()
    autocmd VimEnter,WinEnter * match ZenkakuSpace /　/
    autocmd VimEnter,WinEnter * match ZenkakuSpace '\%u3000'
  augroup END
  call ZenkakuSpace()
endif

"----------------------------------------
" 各種プラグイン設定
"----------------------------------------

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

call plug#begin('~/.vim/plugged')

Plug 'Shougo/deoplete.nvim'
let g:deoplete#enable_at_startup = 1

Plug 'SirVer/ultisnips'
let g:UltiSnipsSnippetDirectories=["UltiSnips", "~/.config/nvim/UltiSnips/"]

Plug 'honza/vim-snippets'
Plug 'thinca/vim-qfreplace'
Plug 'Shougo/deol.nvim'
Plug 'scrooloose/nerdtree'
noremap <leader>fi :NERDTreeToggle<CR>
nnoremap <leader>ft :tabnew<CR>:NERDTreeToggle<CR>
let g:NERDTreeShowHidden=1
let g:NERDTreeShowBookmarks=1

Plug 'whatyouhide/vim-gotham'
Plug 'tpope/vim-fugitive'
Plug 'Xuyuanp/nerdtree-git-plugin'
Plug 'airblade/vim-gitgutter'
Plug 'chriskempson/vim-tomorrow-theme'
Plug 'mopp/mopkai.vim'
Plug 'tomasr/molokai'
Plug 'w0ng/vim-hybrid'
Plug 'jacoborus/tender.vim'
Plug 'vim-airline/vim-airline'
let g:airline_powerline_fonts = 1

Plug 'altercation/vim-colors-solarized'
Plug 'nanotech/jellybeans.vim'
Plug 'w0rp/ale'
Plug 'mattn/emmet-vim'
let g:user_emmet_leader_key='<C-t>'

Plug 'alpaca-tc/html5.vim'
Plug 'othree/html5.vim'
Plug 'mxw/vim-jsx'
Plug 'miya-masa/vim-esformatter'
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
Plug 'elzr/vim-json'
let g:vim_json_syntax_conceal = 0
Plug 'fatih/vim-go', { 'do': ':GoInstallBinaries' }
" vim-go
let g:go_fmt_command = "goimports"
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
let g:go_metalinter_autosave_enabled = ['vet','errcheck', 'golint']
let g:go_metalinter_autosave = 0
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

Plug 'AndrewRadev/splitjoin.vim'
Plug 'jodosha/vim-godebug'
Plug 'zchee/deoplete-go'
let g:deoplete#sources#go#gocode_binary = $GOPATH.'/bin/gocode'
let g:deoplete#sources#go#sort_class = ['package', 'func', 'type', 'var', 'const']

Plug 'kylef/apiblueprint.vim'
Plug 'ekalinin/Dockerfile.vim'

Plug 'yaasita/edit-slack.vim'
if filereadable(expand('~/.vimrc.slack'))
  source ~/.vimrc.slack
endif
command! SlackPG :tabe slack://pg
command! SlackCH :tabe slack://ch
command! SlackDM :tabe slack://dm
command! SlackME :tabe slack://dm/miyauchi.m

Plug 'bkad/CamelCaseMotion'

Plug 'simeji/winresizer'
Plug 'kannokanno/previm'
let g:previm_open_cmd = 'open -a Google\ Chrome'

augroup PrevimSettings
  autocmd!
  autocmd BufNewFile,BufRead *.{md,mdwn,mkd,mkdn,mark*} set filetype=markdown
augroup END

Plug 'vim-scripts/DrawIt'
Plug 'tomtom/tcomment_vim'
Plug 'tpope/vim-surround'
Plug 'bronson/vim-trailing-whitespace'
Plug 'nathanaelkane/vim-indent-guides'
let g:indent_guides_enable_on_vim_startup = 1

Plug 'vim-jp/vimdoc-ja'
Plug 'aklt/plantuml-syntax'
augroup PlantUML
  autocmd!
  au FileType plantuml command! OpenUml :!open -a Google\ Chrome %
augroup END

if !has('nvim')
  Plug 'roxma/nvim-yarp'
  Plug 'roxma/vim-hug-neovim-rpc'
endif

Plug 'vim-scripts/Align'
let g:Align_xstrlen=3

Plug 'vim-scripts/SQLUtilities', {'on' : 'Align'}
let g:sqlutil_align_comma=1

Plug 'cespare/vim-toml'
Plug 'pangloss/vim-javascript'
Plug 'othree/yajs.vim'
Plug 'othree/es.next.syntax.vim'
Plug 'othree/javascript-libraries-syntax.vim'
augroup JavascriptLibrariesSyntax
  autocmd!
  autocmd BufReadPre *.js let b:javascript_lib_use_underscore = 1
  autocmd BufReadPre *.js let b:javascript_lib_use_react = 1
augroup END

Plug 'maxmellon/vim-jsx-pretty'
Plug 'ternjs/tern_for_vim'
Plug 'carlitux/deoplete-ternjs'
let cmd = 'npm install -g term'

" Set bin if you have many instalations
" let g:deoplete#sources#ternjs#tern_bin = '/path/to/tern_bin'
let g:deoplete#sources#ternjs#timeout = 1

" Whether to include the types of the completions in the result data. Default: 0
" let g:deoplete#sources#ternjs#types = 1

" Whether to include the distance (in scopes for variables, in prototypes for
" properties) between the completions and the origin position in the result
" data. Default: 0
" let g:deoplete#sources#ternjs#depths = 1

" Whether to include documentation strings (if found) in the result data.
" Default: 0
" let g:deoplete#sources#ternjs#docs = 1

" When on, only completions that match the current word at the given point will
" be returned. Turn this off to get all results, so that you can filter on the
" client side. Default: 1
"let g:deoplete#sources#ternjs#filter = 0

" Whether to use a case-insensitive compare between the current word and
" potential completions. Default 0
" let g:deoplete#sources#ternjs#case_insensitive = 1

" When completing a property and no completions are found, Tern will use some
" heuristics to try and return some properties anyway. Set this to 0 to
" turn that off. Default: 1
" let g:deoplete#sources#ternjs#guess = 0

" Determines whether the result set will be sorted. Default: 1
" let g:deoplete#sources#ternjs#sort = 0

" When disabled, only the text before the given position is considered part of
" the word. When enabled (the default), the whole variable name that the cursor
" is on will be included. Default: 1
" let g:deoplete#sources#ternjs#expand_word_forward = 0

" Whether to ignore the properties of Object.prototype unless they have been
" spelled out by at least two characters. Default: 1
" let g:deoplete#sources#ternjs#omit_object_prototype = 0

" Whether to include JavaScript keywords when completing something that is not
" a property. Default: 0
" let g:deoplete#sources#ternjs#include_keywords = 1

" If completions should be returned when inside a literal. Default: 1
" let g:deoplete#sources#ternjs#in_literal = 0


"Add extra filetypes
"let g:deoplete#sources#ternjs#filetypes = [
"                \ 'jsx',
"                \ 'javascript.jsx',
"                \ 'vue',
"                \ '...'
"                \ ]

Plug 'jiangmiao/auto-pairs'
Plug 'c9s/perlomni.vim'
Plug 'zchee/deoplete-zsh'
Plug 'skielbasa/vim-material-monokai'
Plug 'felipesousa/rupza'
Plug 'jdkanani/vim-material-theme'
Plug 'morhetz/gruvbox'
Plug 'kristijanhusak/vim-hybrid-material'
Plug 'vim-airline/vim-airline-themes'
Plug 'junegunn/fzf', { 'dir': '~/.fzf', 'do': './install --all' }
nnoremap <Leader><C-B> :Buffer<CR>
nnoremap <Leader><C-A> :Ag<CR>
nnoremap <Leader><C-F> :Files<CR>
nnoremap <leader><C-L> :Line<CR>

Plug 'junegunn/fzf.vim'
Plug 'ryanoasis/vim-devicons'
Plug 'majutsushi/tagbar'
Plug 'dhruvasagar/vim-table-mode'
Plug 'thinca/vim-quickrun'
Plug 'diepm/vim-rest-console'
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

Plug 'osyo-manga/vim-over'
Plug 'flazz/vim-colorschemes'
Plug 'VincentCordobes/vim-translate'
Plug 'fenetikm/falcon'


call plug#end()
call camelcasemotion#CreateMotionMappings('<leader>')

" ###### color scheme
syntax enable
set background=dark
colorscheme gruvbox
let g:airline_theme = 'gruvbox'

" syntax enable
" set background=dark
" set termguicolors
" colorscheme material-
" let g:airline_theme='materialmonokai'
"
"
" # deoplete
" Use smartcase.
call deoplete#custom#option('smart_case', v:true)
inoremap <expr><C-h> deoplete#smart_close_popup()."\<C-h>"
inoremap <expr><BS>  deoplete#smart_close_popup()."\<C-h>"

" conv hex deg bin
command! -nargs=1 ToH echo printf("%0x", <args>)
command! -nargs=1 ToD echo printf("%0d", <args>)
command! -nargs=1 ToB echo printf("%0b", <args>)
command! -nargs=1 ToHReg let @a=printf("%0x", <args>)
command! -nargs=1 ToDReg let @a=printf("%0d", <args>)
command! -nargs=1 ToBReg let @a=printf("%0b", <args>)
