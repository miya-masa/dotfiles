" => General {{{
" Sets how many lines of history VIM has to remember
set history=500

" Enable filetype plugins
filetype plugin on
filetype indent on

" Set to auto read when a file is changed from the outside
set autoread
autocmd FocusGained,BufEnter * checktime

" Share clipboard
set clipboard+=unnamedplus

" viminfo
set viminfo='100,n$HOME/.vim/files/info/viminfo

set formatoptions+=mM

" With a map leader it's possible to do extra key combinations
" like <leader>w saves the current file
let g:mapleader = ","

" Preview substitute
set inccommand=split
set ambiwidth=single

set list
set listchars=tab:^\ ,trail:~

" }}}
" => VIM user interface {{{

" Set 7 lines to the cursor - when moving vertically using j/k
set scrolloff=7

" Display line number
set number

" Use '/' instead of '\' when windows.
set shellslash

"   lastline  When included, as much as possible of the last line
"       in a window will be displayed.  "@@@" is put in the
"       last columns of the last screen line to indicate the
"       rest of the line is not displayed.
set display=lastline

" Avoid garbled characters in Chinese language windows OS
scriptencoding utf8
set helplang=ja,en
let $LANG='ja_JP.UTF-8'
source $VIMRUNTIME/delmenu.vim
set langmenu=ja_JP.UTF-8
source $VIMRUNTIME/menu.vim

" Turn on the Wild menu
set wildmenu

" Ignore compiled files
set wildignore=*.o,*~,*.pyc
if has("win16") || has("win32")
    set wildignore+=.git\*,.hg\*,.svn\*
else
    set wildignore+=*/.git/*,*/.hg/*,*/.svn/*,*/.DS_Store
endif

"Always show current position
set ruler

" Height of the command bar
set cmdheight=2

" A buffer becomes hidden when it is abandoned
set hidden

" Configure backspace so it acts as it should act
set backspace=eol,start,indent

set whichwrap=b,s,[,],<,>

" Ignore case when searching
set ignorecase

" When searching try to be smart about cases
set smartcase

" Highlight search results
set hlsearch

" Makes search act like search in modern browsers
set incsearch

" Don't redraw while executing macros (good performance config)
set lazyredraw

" For regular expressions turn magic on
set magic

" Show matching brackets when text indicator is over them
set showmatch
" How many tenths of a second to blink when matching brackets
set matchtime=2

" No annoying sound on errors
set noerrorbells
set novisualbell
set t_vb=
set timeoutlen=500

" Properly disable sound on errors on MacVim
if has("gui_macvim")
    autocmd GUIEnter * set vb t_vb=
endif


" Add a bit extra margin to the left
set foldcolumn=1
" }}}
" => Files, backups and undo {{{
" Turn backup off, since most stuff is in SVN, git et.c anyway...
set nobackup
set nowritebackup
set noswapfile
" }}}
" => Text, tab and indent related {{{

" Use spaces instead of tabs
set expandtab

" Be smart when using tabs ;)
set smarttab

" 1 tab == 2 spaces
set shiftwidth=2
set softtabstop=2
set tabstop=4

" Linebreak on 500 characters
set linebreak
set tw=500

set autoindent "Auto indent
set smartindent "Smart indent
set wrap "Wrap lines
" }}}
" => Visual mode related {{{

" Visual mode pressing * or # searches for the current selection
" Super useful! From an idea by Michael Naumann
vnoremap <silent> * :<C-u>call VisualSelection('', '')<CR>/<C-R>=@/<CR><CR>
vnoremap <silent> # :<C-u>call VisualSelection('', '')<CR>?<C-R>=@/<CR><CR>

" }}}
" => Moving around, tabs, windows and buffers {{{

" Disable highlight when <leader><cr> is pressed
map <silent> <leader><cr> :noh<cr>

" Smart way to move between windows
map <C-j> <C-W>j
map <C-k> <C-W>k
map <C-h> <C-W>h
map <C-l> <C-W>l

" Close the current buffer
map <leader>bd :Bclose<cr>:tabclose<cr>gT

" Close all the buffers
map <leader>ba :bufdo bd<cr>

" Let 'tl' toggle between this and the last accessed tab
let g:lasttab = 1
nmap <Leader>tl :exe "tabn ".g:lasttab<CR>
au TabLeave * let g:lasttab = tabpagenr()

" Switch CWD to the directory of the open buffer
map <leader>cd :cd %:p:h<cr>:pwd<cr>

" Specify the behavior when switching between buffers
try
  set switchbuf=useopen,usetab,split
" Display tabline with one or more tabs.
  set stal=1
catch
endtry

" }}}
" => Status line {{{
" Always show the status line
set laststatus=2
" }}}
" => Editing mappings {{{
" Remap VIM 0 to first non-blank character
map 0 ^
" }}}
" => Spell checking {{{
" Pressing ,ss will toggle and untoggle spell checking
map <leader>ss :setlocal spell!<cr>

" Shortcuts using <leader>
map <leader>sa zg
map <leader>s? z=
" }}}
" => Misc {{{
" Remove the Windows ^M - when the encodings gets messed up
noremap <Leader>m mmHmt:%s/<C-V><cr>//ge<cr>'tzt'm

" Quickly open a buffer for scribble
map <leader>q :e ~/buffer<cr>

" Quickly open a markdown buffer for scribble
map <leader>x :e ~/buffer.md<cr>

" }}}
" => Helper functions {{{
" Don't close window, when deleting a buffer
command! Bclose call <SID>BufcloseCloseIt()
function! <SID>BufcloseCloseIt()
    let l:currentBufNum = bufnr("%")
    let l:alternateBufNum = bufnr("#")

    if buflisted(l:alternateBufNum)
        buffer #
    else
        bnext
    endif

    if bufnr("%") == l:currentBufNum
        new
    endif

    if buflisted(l:currentBufNum)
        execute("bdelete! ".l:currentBufNum)
    endif
endfunction

function! CmdLine(str)
    call feedkeys(":" . a:str)
endfunction

function! VisualSelection(direction, extra_filter) range
    let l:saved_reg = @"
    execute "normal! vgvy"

    let l:pattern = escape(@", "\\/.*'$^~[]")
    let l:pattern = substitute(l:pattern, "\n$", "", "")

    if a:direction == 'gv'
        call CmdLine("Ack '" . l:pattern . "' " )
    elseif a:direction == 'replace'
        call CmdLine("%s" . '/'. l:pattern . '/')
    endif

    let @/ = l:pattern
    let @" = l:saved_reg
endfunction

command! -nargs=1 ToH echo printf("%0x", <args>)
command! -nargs=1 ToD echo printf("%0d", <args>)
command! -nargs=1 ToB echo printf("%0b", <args>)
command! -nargs=1 ToHRegA let @a=printf("%0x", <args>)
command! -nargs=1 ToDRegA let @a=printf("%0d", <args>)
command! -nargs=1 ToBRegA let @a=printf("%0b", <args>)
command! Si :call SelfImport()

function! SelfImport()
  let bufPath = expand("%:p")
  let fileName = substitute(expand("%"), expand("%:h") . "/", "", "g")
  let importPath = substitute(substitute(bufPath, $GOPATH . "/src/", "", "g"),"/" . fileName, "", "g")
  let selfImport = ". \"" . importPath . "\""

  let pos = getpos(".")
  execute ":normal i" . selfImport
  :call setpos('.', pos)

endfunction
" }}}
