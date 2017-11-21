scriptencoding utf8
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
set clipboard+=unnamed
" 8進数を無効にする。<C-a>,<C-x>に影響する
set nrformats-=octal
" キーコードやマッピングされたキー列が完了するのを待つ時間(ミリ秒)
set timeout timeoutlen=3000 ttimeoutlen=500
" 編集結果非保存のバッファから、新しいバッファを開くときに警告を出さない
set hidden
" ヒストリの保存数
set history=50
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
" set cmdheight=2
set laststatus=2
" コマンドをステータス行に表示
set showcmd
" 画面最後の行をできる限り表示する
set display=lastline
" Tab、行末の半角スペースを明示的に表示する
set list
set listchars=tab:^\ ,trail:~

" ハイライトを有効にする
if &t_Co > 2 || has('gui_running')
  syntax on
endif

""""""""""""""""""""""""""""""
" ステータスラインに文字コード等表示
" iconvが使用可能の場合、カーソル上の文字コードをエンコードに応じた表示にするFencB()を使用
""""""""""""""""""""""""""""""
if has('iconv')
  set statusline=%<%f\ %m\ %r%h%w%{'['.(&fenc!=''?&fenc:&enc).']['.&ff.']'}%=[0x%{FencB()}]\ (%v,%l)/%L%8P\
else
  set statusline=%<%f\ %m\ %r%h%w%{'['.(&fenc!=''?&fenc:&enc).']['.&ff.']'}%=\ (%v,%l)/%L%8P\
endif

" FencB() : カーソル上の文字コードをエンコードに応じた表示にする
function! FencB()
  let c = matchstr(getline('.'), '.', col('.') - 1)
  let c = iconv(c, &enc, &fenc)
  return s:Byte2hex(s:Str2byte(c))
endfunction

function! s:Str2byte(str)
  return map(range(len(a:str)), 'char2nr(a:str[v:val])')
endfunction

function! s:Byte2hex(bytes)
  return join(map(copy(a:bytes), 'printf("%02X", v:val)'), '')
endfunction

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
vnoremap H ^
vnoremap L g_
nnoremap <C-j> <C-W>j
nnoremap <C-k> <C-W>k
nnoremap <C-h> <C-W>h
nnoremap <C-l> <C-W>l
nnoremap <leader><space> :nohlsearch<CR>

" Some useful quickfix shortcuts for quickfix
nnoremap <C-n> :cn<CR>
nnoremap <C-m> :cp<CR>
nnoremap <leader>a :cclose<CR>

" vimshell 
tnoremap <silent> <ESC> <C-\><C-n>
nnoremap <leader>vt :tabnew<CR>:terminal<CR>

" denite
nnoremap <leader>db :Denite buffer<CR>
nnoremap <leader>dg :Denite grep<CR>
nnoremap <leader>df :Denite file_rec<CR>
nnoremap <leader>dl :Denite line<CR>

"----------------------------------------
" 挿入モード
"----------------------------------------

"----------------------------------------
" ビジュアルモード
"----------------------------------------

"----------------------------------------
" コマンドモード
"----------------------------------------

"----------------------------------------
" Vimスクリプト
"----------------------------------------

""""""""""""""""""""""""""""""
" ファイルを開いたら前回のカーソル位置へ移動
""""""""""""""""""""""""""""""
augroup vimrcEx
  autocmd!
  autocmd BufReadPost * if line("'\"") > 1 && line("'\"") <= line('$') | exe "normal! g`\"" | endif
augroup END

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

"dein Scripts-----------------------------
if &compatible
  set nocompatible               " Be iMproved
endif

" Required:
set runtimepath+=/Users/miyauchi-masayuki/.nvim/repos/github.com/Shougo/dein.vim

" Required:
if dein#load_state('/Users/miyauchi-masayuki/.nvim')
  call dein#begin('/Users/miyauchi-masayuki/.nvim')
  " Required:
  call dein#add('~/.vim/bundles/repos/github.com/Shougo/dein.vim')

  " Add or remove your plugins here:
  call dein#add('Shougo/deoplete.nvim')
  if !has('nvim')
    call dein#add('roxma/nvim-yarp')
    call dein#add('roxma/vim-hug-neovim-rpc')
  endif
  " snippet
  call dein#add('SirVer/ultisnips')

  " Unite 
  call dein#add('Shougo/unite-outline')
  call dein#add('Shougo/denite.nvim')
  call dein#add('thinca/vim-qfreplace')
  call dein#add('tpope/vim-fugitive')
  call dein#add('Shougo/deol.nvim')

  " nerdtree
  call dein#add('scrooloose/nerdtree')
  call dein#add('Xuyuanp/nerdtree-git-plugin')

  " colorscheme
  call dein#add('chriskempson/vim-tomorrow-theme')
  call dein#add('mopp/mopkai.vim')
  call dein#add('fatih/molokai')
  " syntax
  call dein#add('vim-syntastic/syntastic')

  " Html5 snipetts
  call dein#add('mattn/emmet-vim')
  " Html5 omnicomplete
  call dein#add('alpaca-tc/html5.vim')
  call dein#add('othree/html5.vim')

  " JS
  call dein#add('mxw/vim-jsx')
  call dein#add('miya-masa/vim-esformatter')
  " JSON
  call dein#add('elzr/vim-json')


  " go
  call dein#add('fatih/vim-go')
  call dein#add('AndrewRadev/splitjoin.vim')
  call dein#add('ctrlpvim/ctrlp.vim')
  call dein#add('jodosha/vim-godebug')
  call dein#add('zchee/deoplete-go', {'build': 'make'})

  " apiblueprint
  call dein#add('kylef/apiblueprint.vim')

  " Docker
  call dein#add('ekalinin/Dockerfile.vim')

  " Slack
  call dein#add('yaasita/edit-slack.vim')

  " other
  call dein#add('majutsushi/tagbar')
  call dein#add('bkad/CamelCaseMotion')
  call dein#add('simeji/winresizer')
  call dein#add('kannokanno/previm')
  call dein#add('vim-scripts/DrawIt')

  " Required:
  call dein#end()
  call dein#save_state()
endif

" Required:
syntax enable

" If you want to install not installed plugins on startup.
if dein#check_install()
  call dein#install()
endif

"End dein Scripts-------------------------

" #######################
" start nerdtree
" #######################
noremap <leader>fi :NERDTreeToggle<CR>
nnoremap <leader>ft :tabnew<CR>:NERDTreeToggle<CR>
let NERDTreeShowHidden=1
let NERDTreeShowBookmarks=1

" #######################
" start ultisnips
" #######################

let g:UltiSnipsSnippetDirectories=["UltiSnips", "~/.config/nvim/UltiSnips/"]

" #######################
" start web
" #######################
" for html
autocmd FileType html,hbs noremap <buffer> <c-f> :call HtmlBeautify()<cr>
" for css or scss
autocmd FileType css noremap <buffer> <c-f> :call CSSBeautify()<cr>
" My Bundles here:

" will run esformatter after pressing <leader> followed by the 'e' and 's' keys
autocmd FileType javascript noremap <silent>  <c-f> :Esformatter<CR>
autocmd FileType javascript vnoremap <silent>  <c-f> :EsformatterVisual<CR>

let g:user_emmet_leader_key='<C-t>'


" #######################
" start syntastic
" #######################

set statusline+=%#warningmsg#
set statusline+=%{SyntasticStatuslineFlag()}
set statusline+=%*

let g:syntastic_always_populate_loc_list = 1
let g:syntastic_auto_loc_list = 1
let g:syntastic_check_on_open = 1
let g:syntastic_check_on_wq = 0
let g:syntastic_javascript_checkers = ["eslint"]


" #######################
" start go
" #######################

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
let g:go_metalinter_autosave_enabled = ['vet', 'golint', 'errcheck']
let g:go_metalinter_autosave = 1
let g:go_def_mode = 'godef'
let g:go_term_mode = 'vsplit'

" Guru Scope
let g:go_guru_scope = ["git.aptpod.co.jp/intdash/intdash-api/api/..." ,"git.aptpod.co.jp/intdash/intdash-api/api/...","git.aptpod.co.jp/intdash/intdash-api/cmd/...","git.aptpod.co.jp/intdash/intdash-api/pubsub/...","git.aptpod.co.jp/intdash/intdash-api/rdb/...","git.aptpod.co.jp/intdash/intdash-api/tsdb/...","git.aptpod.co.jp/intdash/intdash-api/ws/..."]

" Open :GoDeclsDir with ctrl-g
nmap <C-g> :GoDeclsDir<cr>
imap <C-g> <esc>:<C-u>GoDeclsDir<cr>


augroup go
  autocmd!
  " Show by default 4 spaces for a tab
  autocmd BufNewFile,BufRead *.go setlocal noexpandtab tabstop=4 shiftwidth=4
  " :GoBuild and :GoTestCompile
  autocmd FileType go nmap <leader>b :<C-u>call <SID>build_go_files()<CR>
  " :GoTest
  autocmd FileType go nmap <leader>t  <Plug>(go-test)
  " :GoRun
  autocmd FileType go nmap <leader>r  <Plug>(go-run)
  " :GoDoc
  autocmd FileType go nmap <Leader>d <Plug>(go-doc)
  " :GoCoverageToggle
  autocmd FileType go nmap <Leader>c <Plug>(go-coverage-toggle)
  " :GoInfo
  autocmd FileType go nmap <Leader>i <Plug>(go-info)
  " :GoMetaLinter
  autocmd FileType go nmap <Leader>l <Plug>(go-metalinter)
  " :GoDef but opens in a vertical split
  autocmd FileType go nmap <Leader>v <Plug>(go-def-vertical)
  " :GoDef but opens in a horizontal split
  autocmd FileType go nmap <Leader>ss <Plug>(go-def-split)
  " :GoTestFunc
  autocmd FileType go nmap <Leader>ff <Plug>(go-test-func)

  " :GoAlternate  commands :A, :AV, :AS and :AT
  autocmd Filetype go command! -bang A call go#alternate#Switch(<bang>0, 'edit')
  autocmd Filetype go command! -bang AV call go#alternate#Switch(<bang>0, 'vsplit')
  autocmd Filetype go command! -bang AS call go#alternate#Switch(<bang>0, 'split')
  autocmd Filetype go command! -bang AT call go#alternate#Switch(<bang>0, 'tabe')
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



" #######################
" start previm
" #######################
let g:previm_open_cmd = 'open -a Google\ Chrome'

augroup PrevimSettings
    autocmd!
    autocmd BufNewFile,BufRead *.{md,mdwn,mkd,mkdn,mark*} set filetype=markdown
augroup END


" #######################
" start json
" #######################
let g:vim_json_syntax_conceal = 0


" #######################
" start deoplete
" #######################
" Use deoplete.
let g:deoplete#enable_at_startup = 1


" #######################
" start color
" #######################
let g:rehash256 = 1
let g:molokai_original = 1
colorscheme molokai


" #######################
" start denite  
" #######################
	" Change file_rec command.
	call denite#custom#var('file_rec', 'command',
	\ ['ag', '--follow', '--nocolor', '--nogroup', '-g', ''])
"	" For ripgrep
"	" Note: It is slower than ag
"	call denite#custom#var('file_rec', 'command',
"	\ ['rg', '--files', '--glob', '!.git', ''])
"	" For Pt(the platinum searcher)
"	" NOTE: It also supports windows.
"	call denite#custom#var('file_rec', 'command',
"	\ ['pt', '--follow', '--nocolor', '--nogroup',
"	\  (has('win32') ? '-g:' : '-g='), ''])
"	"For python script scantree.py (works if python 3.5+ in path)
"	"Read bellow on this file to learn more about scantree.py
"	call denite#custom#var('file_rec', 'command', ['scantree.py'])

	" Change mappings.
	call denite#custom#map(
	      \ 'insert',
	      \ '<C-j>',
	      \ '<denite:move_to_next_line>',
	      \ 'noremap'
	      \)
	call denite#custom#map(
	      \ 'insert',
	      \ '<C-k>',
	      \ '<denite:move_to_previous_line>',
	      \ 'noremap'
	      \)

	" Change matchers.
	call denite#custom#source(
	\ 'file_mru', 'matchers', ['matcher_fuzzy', 'matcher_project_files'])
	call denite#custom#source(
	\ 'file_rec', 'matchers', ['matcher_cpsm'])

	" Change sorters.
	call denite#custom#source(
	\ 'file_rec', 'sorters', ['sorter_sublime'])

	" Add custom menus
"	let s:menus = {}
"
"	let s:menus.zsh = {
"		\ 'description': 'Edit your import zsh configuration'
"		\ }
"	let s:menus.zsh.file_candidates = [
"		\ ['zshrc', '~/.config/zsh/.zshrc'],
"		\ ['zshenv', '~/.zshenv'],
"		\ ]
"
"	let s:menus.my_commands = {
"		\ 'description': 'Example commands'
"		\ }
"	let s:menus.my_commands.command_candidates = [
"		\ ['Split the window', 'vnew'],
"		\ ['Open zsh menu', 'Denite menu:zsh'],
"		\ ]

"	call denite#custom#var('menu', 'menus', s:menus)

	" Ag command on grep source
	call denite#custom#var('grep', 'command', ['ag'])
	call denite#custom#var('grep', 'default_opts',
			\ ['-i', '--vimgrep'])
	call denite#custom#var('grep', 'recursive_opts', [])
	call denite#custom#var('grep', 'pattern_opt', [])
	call denite#custom#var('grep', 'separator', ['--'])
	call denite#custom#var('grep', 'final_opts', [])

"	" Ack command on grep source
"	call denite#custom#var('grep', 'command', ['ack'])
"	call denite#custom#var('grep', 'default_opts',
"			\ ['--ackrc', $HOME.'/.ackrc', '-H',
"			\  '--nopager', '--nocolor', '--nogroup', '--column'])
"	call denite#custom#var('grep', 'recursive_opts', [])
"	call denite#custom#var('grep', 'pattern_opt', ['--match'])
"	call denite#custom#var('grep', 'separator', ['--'])
"	call denite#custom#var('grep', 'final_opts', [])

"	" Ripgrep command on grep source
"	call denite#custom#var('grep', 'command', ['rg'])
"	call denite#custom#var('grep', 'default_opts',
"			\ ['--vimgrep', '--no-heading'])
"	call denite#custom#var('grep', 'recursive_opts', [])
"	call denite#custom#var('grep', 'pattern_opt', ['--regexp'])
"	call denite#custom#var('grep', 'separator', ['--'])
"	call denite#custom#var('grep', 'final_opts', [])

	" Pt command on grep source
"	call denite#custom#var('grep', 'command', ['pt'])
"	call denite#custom#var('grep', 'default_opts',
"			\ ['--nogroup', '--nocolor', '--smart-case'])
"	call denite#custom#var('grep', 'recursive_opts', [])
"	call denite#custom#var('grep', 'pattern_opt', [])
"	call denite#custom#var('grep', 'separator', ['--'])
"	call denite#custom#var('grep', 'final_opts', [])
"
"	" jvgrep command on grep source
"	call denite#custom#var('grep', 'command', ['jvgrep'])
"	call denite#custom#var('grep', 'default_opts', [])
"	call denite#custom#var('grep', 'recursive_opts', ['-R'])
"	call denite#custom#var('grep', 'pattern_opt', [])
"	call denite#custom#var('grep', 'separator', [])
"	call denite#custom#var('grep', 'final_opts', [])

	" Define alias
	call denite#custom#alias('source', 'file_rec/git', 'file_rec')
	call denite#custom#var('file_rec/git', 'command',
	      \ ['git', 'ls-files', '-co', '--exclude-standard'])

	call denite#custom#alias('source', 'file_rec/py', 'file_rec')
	call denite#custom#var('file_rec/py', 'command',['scantree.py'])

	" Change default prompt
	call denite#custom#option('default', 'prompt', '>')

	" Change ignore_globs
	call denite#custom#filter('matcher_ignore_globs', 'ignore_globs',
	      \ [ '.git/', '.ropeproject/', '__pycache__/',
	      \   'venv/', 'images/', '*.min.*', 'img/', 'fonts/'])

	" Custom action
"	call denite#custom#action('file', 'test',
"	      \ {context -> execute('let g:foo = 1')})
"	call denite#custom#action('file', 'test2',
"	      \ {context -> denite#do_action(
"	      \  context, 'open', context['targets'])})
"
"
" #######################
" start camel motion  
" #######################
call camelcasemotion#CreateMotionMappings('<leader>')


" #######################
" start Slack vim
" #######################
"
if filereadable(expand('~/.vimrc.slack'))
source ~/.vimrc.slack
endif

" #######################
" start deoplete go
" #######################

let g:deoplete#sources#go#gocode_binary = $GOPATH.'/bin/gocode'
let g:deoplete#sources#go#sort_class = ['package', 'func', 'type', 'var', 'const']
