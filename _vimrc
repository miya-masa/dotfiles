"=============================================================================
"    Description: .vimrc�T���v���ݒ�
"         Author: anonymous
"  Last Modified: 0000-00-00 00:00
"        Version: 7.40
"=============================================================================
set nocompatible
scriptencoding cp932
" scriptencoding�ƁA���̃t�@�C���̃G���R�[�f�B���O����v����悤���ӁI
" scriptencoding�́Avim�̓����G���R�[�f�B���O�Ɠ������̂𐄏����܂��B
" ���s�R�[�h�� set fileformat=unix �ɐݒ肷���unix�ł��g���܂��B

" Windows�œ����G���R�[�f�B���O�� cp932�ȊO�ɂ��Ă��āA
" ���ϐ��ɓ��{����܂ޒl��ݒ肵�����ꍇ�� Let ���g�p���܂��B
" Let�� vimrc(�I�[���C�������p�b�P�[�W�̏ꍇ)�� encode.vim �Œ�`����܂��B
" Let $HOGE=$USERPROFILE.'/�ق�'

"----------------------------------------
" ���[�U�[�����^�C���p�X�ݒ�
"----------------------------------------
" Windows, unix�ł�runtimepath�̈Ⴂ���z�����邽�߂̂��́B
" $MY_VIMRUNTIME�̓��[�U�[�����^�C���f�B���N�g���������B
" :echo $MY_VIMRUNTIME�Ŏ��ۂ̃p�X���m�F�ł��܂��B
if isdirectory($HOME . '/.vim')
  let $MY_VIMRUNTIME = $HOME.'/.vim'
elseif isdirectory($HOME . '\vimfiles')
  let $MY_VIMRUNTIME = $HOME.'\vimfiles'
elseif isdirectory($VIM . '\vimfiles')
  let $MY_VIMRUNTIME = $VIM.'\vimfiles'
endif

" �����^�C���p�X��ʂ��K�v�̂���v���O�C�����g�p����ꍇ�A
" $MY_VIMRUNTIME���g�p����� Windows/Linux�Ő؂蕪����K�v�������Ȃ�܂��B
" ��) vimfiles/qfixapp (Linux�ł�~/.vim/qfixapp)�Ƀ����^�C���p�X��ʂ��ꍇ
" set runtimepath+=$MY_VIMRUNTIME/qfixapp

"----------------------------------------
" �����G���R�[�f�B���O�w��
"----------------------------------------
" �����G���R�[�f�B���O��UTF-8���ƕ����R�[�h�̎����F���ݒ��encode.vim�ōs���B
" �I�[���C�������p�b�P�[�W�̏ꍇ vimrc�Őݒ肳��܂��B
" �G���R�[�f�B���O�w��╶���R�[�h�̎����F���ݒ肪�K�؂ɐݒ肳��Ă���ꍇ�A
" ���s�� encode.vim�Ǎ������̓R�����g�A�E�g���ĉ������B
" silent! source $MY_VIMRUNTIME/pluginjp/encode.vim
" scriptencoding�ƈقȂ�����G���R�[�f�B���O�ɕύX����ꍇ�A
" �ύX��ɂ�scriptencoding���w�肵�Ă����Ɩ�肪�N���ɂ����Ȃ�܂��B
" scriptencoding cp932

"----------------------------------------
" �V�X�e���ݒ�
"----------------------------------------
" mswin.vim��ǂݍ���
" source $VIMRUNTIME/mswin.vim
" behave mswin

" �t�@�C���̏㏑���̑O�Ƀo�b�N�A�b�v�����/���Ȃ�
" set writebackup���w�肵�Ă��I�v�V���� 'backup' ���I���łȂ�����A
" �o�b�N�A�b�v�͏㏑���ɐ���������ɍ폜�����B
set nowritebackup
" �o�b�N�A�b�v/�X���b�v�t�@�C�����쐬����/���Ȃ�
set nobackup
if version >= 703
  " �ēǍ��Avim�I������p������A���h�D(7.3)
  " set undofile
  " �A���h�D�̕ۑ��ꏊ(7.3)
  " set undodir=.
endif
 set noswapfile
" viminfo���쐬���Ȃ�
" set viminfo=
" �N���b�v�{�[�h�����L
set clipboard+=unnamed
" 8�i���𖳌��ɂ���B<C-a>,<C-x>�ɉe������
set nrformats-=octal
" �L�[�R�[�h��}�b�s���O���ꂽ�L�[�񂪊�������̂�҂���(�~���b)
set timeout timeoutlen=3000 ttimeoutlen=100
" �ҏW���ʔ�ۑ��̃o�b�t�@����A�V�����o�b�t�@���J���Ƃ��Ɍx�����o���Ȃ�
set hidden
" �q�X�g���̕ۑ���
set history=50
" ���{��̍s�̘A�����ɂ͋󔒂���͂��Ȃ�
set formatoptions+=mM
" Visual block���[�h�Ńt���[�J�[�\����L���ɂ���
set virtualedit=block
" �J�[�\���L�[�ōs���^�s���̈ړ��\�ɐݒ�
set whichwrap=b,s,[,],<,>
" �o�b�N�X�y�[�X�ŃC���f���g����s���폜�ł���悤�ɂ���
set backspace=indent,eol,start
" ���⁛�̕����������Ă��J�[�\���ʒu������Ȃ��悤�ɂ���
set ambiwidth=double
" �R�}���h���C���⊮����Ƃ��ɋ������ꂽ���̂��g��
set wildmenu
" �}�E�X��L���ɂ���
if has('mouse')
  set mouse=a
endif
" plugin���g�p�\�ɂ���
filetype plugin indent on

"----------------------------------------
" ����
"----------------------------------------
" �����̎��ɑ啶������������ʂ��Ȃ�
" �������啶���������̗������܂܂�Ă���ꍇ�͑啶������������ʂ���
set ignorecase
set smartcase
" �������Ƀt�@�C���̍Ō�܂ōs������ŏ��ɖ߂�
set wrapscan
" �C���N�������^���T�[�`
set incsearch
" ���������̋����\��
set hlsearch
" w,b�̈ړ��ŔF�����镶��
" set iskeyword=a-z,A-Z,48-57,_,.,-,>
" vimgrep ���f�t�H���g��grep�Ƃ���ꍇinternal
" set grepprg=internal

"----------------------------------------
" �\���ݒ�
"----------------------------------------
" �X�v���b�V��(�N�����̃��b�Z�[�W)��\�����Ȃ�
" set shortmess+=I
" �G���[���̉��ƃr�W���A���x���̗}��(gvim��.gvimrc�Őݒ�)
set noerrorbells
set novisualbell
set visualbell t_vb=
" �}�N�����s���Ȃǂ̉�ʍĕ`����s��Ȃ�
" WindowsXp�܂���Window�e�[�}���uWindows�N���V�b�N�v��
" Google���{����͂��g�p�����I�r�[���J�[�\�����c��ꍇ�ɂ��L��
" set lazyredraw
" Windows�Ńf�B���N�g���p�X�̋�؂蕶���\���� / ���g����悤�ɂ���
set shellslash
" �s�ԍ��\��
set number
if version >= 703
  " ���΍s�ԍ��\��(7.3)
  " set relativenumber
endif
" ���ʂ̑Ή��\������
set showmatch matchtime=1
" �^�u��ݒ�
" set ts=4 sw=4 sts=4
" �����I�ɃC���f���g����
set autoindent
" C�C���f���g�̐ݒ�
set cinoptions+=:0
" �^�C�g����\��
set title
" �R�}���h���C���̍��� (gvim��gvimrc�Ŏw��)
" set cmdheight=2
set laststatus=2
" �R�}���h���X�e�[�^�X�s�ɕ\��
set showcmd
" ��ʍŌ�̍s���ł������\������
set display=lastline
" Tab�A�s���̔��p�X�y�[�X�𖾎��I�ɕ\������
set list
set listchars=tab:^\ ,trail:~

" �n�C���C�g��L���ɂ���
if &t_Co > 2 || has('gui_running')
  syntax on
endif
" �F�e�[�}�ݒ�
" gvim�̐F�e�[�}��.gvimrc�Ŏw�肷��
" colorscheme mylight

""""""""""""""""""""""""""""""
" �X�e�[�^�X���C���ɕ����R�[�h���\��
" iconv���g�p�\�̏ꍇ�A�J�[�\����̕����R�[�h���G���R�[�h�ɉ������\���ɂ���FencB()���g�p
""""""""""""""""""""""""""""""
if has('iconv')
  set statusline=%<%f\ %m\ %r%h%w%{'['.(&fenc!=''?&fenc:&enc).']['.&ff.']'}%=[0x%{FencB()}]\ (%v,%l)/%L%8P\ 
else
  set statusline=%<%f\ %m\ %r%h%w%{'['.(&fenc!=''?&fenc:&enc).']['.&ff.']'}%=\ (%v,%l)/%L%8P\ 
endif

" FencB() : �J�[�\����̕����R�[�h���G���R�[�h�ɉ������\���ɂ���
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
" diff/patch
"----------------------------------------
" diff�̐ݒ�
if has('win32') || has('win64')
  set diffexpr=MyDiff()
  function! MyDiff()
    " 7.3.443 �ȍ~�̕ύX�ɑΉ�
    silent! let saved_sxq=&shellxquote
    silent! set shellxquote=
    let opt = '-a --binary '
    if &diffopt =~ 'icase' | let opt = opt . '-i ' | endif
    if &diffopt =~ 'iwhite' | let opt = opt . '-b ' | endif
    let arg1 = v:fname_in
    if arg1 =~ ' ' | let arg1 = '"' . arg1 . '"' | endif
    let arg2 = v:fname_new
    if arg2 =~ ' ' | let arg2 = '"' . arg2 . '"' | endif
    let arg3 = v:fname_out
    if arg3 =~ ' ' | let arg3 = '"' . arg3 . '"' | endif
    let cmd = '!diff ' . opt . arg1 . ' ' . arg2 . ' > ' . arg3
    silent execute cmd
    silent! let &shellxquote = saved_sxq
  endfunction
endif

" ���o�b�t�@�̍����\��(�ύX�ӏ��̕\��)
command! DiffOrig vert new | set bt=nofile | r ++edit # | 0d_ | diffthis | wincmd p | diffthis
" �t�@�C���܂��̓o�b�t�@�ԍ����w�肵�č����\���B#�Ȃ痠�o�b�t�@�Ɣ�r
command! -nargs=? -complete=file Diff if '<args>'=='' | browse vertical diffsplit|else| vertical diffsplit <args>|endif
" �p�b�`�R�}���h
set patchexpr=MyPatch()
function! MyPatch()
   call system($VIM."\\'.'patch -o " . v:fname_out . " " . v:fname_in . " < " . v:fname_diff)
endfunction

set tabstop=2
set shiftwidth=2
set expandtab
"----------------------------------------
" �m�[�}�����[�h
"----------------------------------------
" �w���v����
nnoremap <F1> K
" ���݊J���Ă���vim�X�N���v�g�t�@�C�������s
nnoremap <F8> :source %<CR>
" �����S�ۑ��I���𖳌���
nnoremap ZZ <Nop>
" �J�[�\����j k �ł͕\���s�ňړ�����B�����s�ړ���<C-n>,<C-p>
" �L�[�{�[�h�}�N���ɂ͕����s�ړ��𐄏�
" h l �͍s���A�s���𒴂��邱�Ƃ��\�ɐݒ�(whichwrap)
nnoremap <Down> gj
nnoremap <Up>   gk
nnoremap h <Left>zv
nnoremap j gj
nnoremap k gk
nnoremap l <Right>zv
nnoremap ,pt <Esc>:%! perltidy -se<CR>
nnoremap ,uh <Esc>:Unite history/yank<CR>
nnoremap ,ub <Esc>:Unite bookmark<CR>
nnoremap ,tp <Esc>:tabprevious<CR>
nnoremap ,tn <Esc>:tabNext<CR>

"----------------------------------------
" �}�����[�h
"----------------------------------------

"----------------------------------------
" �r�W���A�����[�h
"----------------------------------------
vnoremap ,pt <Esc>:'<,'>! perltidy -se<CR>
"----------------------------------------
" �R�}���h���[�h
"----------------------------------------

"----------------------------------------
" Vim�X�N���v�g
"----------------------------------------
""""""""""""""""""""""""""""""
" �t�@�C�����J������O��̃J�[�\���ʒu�ֈړ�
" $VIMRUNTIME/vimrc_example.vim
""""""""""""""""""""""""""""""
augroup vimrcEx
  autocmd!
  autocmd BufReadPost * if line("'\"") > 1 && line("'\"") <= line('$') | exe "normal! g`\"" | endif
augroup END

""""""""""""""""""""""""""""""
" �}�����[�h���A�X�e�[�^�X���C���̃J���[�ύX
""""""""""""""""""""""""""""""
let g:hi_insert = 'highlight StatusLine guifg=darkblue guibg=darkyellow gui=none ctermfg=blue ctermbg=yellow cterm=none'

if has('syntax')
  augroup InsertHook
    autocmd!
    autocmd InsertEnter * call s:StatusLine('Enter')
    autocmd InsertLeave * call s:StatusLine('Leave')
  augroup END
endif
" if has('unix') && !has('gui_running')
"   " ESC�ł����ɔ��f����Ȃ��΍�
"   inoremap <silent> <ESC> <ESC>
" endif

let s:slhlcmd = ''
function! s:StatusLine(mode)
  if a:mode == 'Enter'
    silent! let s:slhlcmd = 'highlight ' . s:GetHighlight('StatusLine')
    silent exec g:hi_insert
  else
    highlight clear StatusLine
    silent exec s:slhlcmd
    redraw
  endif
endfunction

function! s:GetHighlight(hi)
  redir => hl
  exec 'highlight '.a:hi
  redir END
  let hl = substitute(hl, '[\r\n]', '', 'g')
  let hl = substitute(hl, 'xxx', '', '')
  return hl
endfunction

""""""""""""""""""""""""""""""
" �S�p�X�y�[�X��\��
""""""""""""""""""""""""""""""
" �R�����g�ȊO�őS�p�X�y�[�X���w�肵�Ă���̂ŁAscriptencoding�ƁA
" ���̃t�@�C���̃G���R�[�h����v����悤���ӁI
" �����\������Ȃ��ꍇ�A������scriptencoding���w�肷��Ƃ��܂�������������܂��B
" scriptencoding cp932
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
    autocmd VimEnter,WinEnter * match ZenkakuSpace /�@/
  augroup END
  call ZenkakuSpace()
endif

""""""""""""""""""""""""""""""
" grep,tags�̂��߃J�����g�f�B���N�g�����t�@�C���Ɠ����f�B���N�g���Ɉړ�����
""""""""""""""""""""""""""""""
" if exists('+autochdir')
"   "autochdir������ꍇ�J�����g�f�B���N�g�����ړ�
"   set autochdir
" else
"   "autochdir�����݂��Ȃ����A�J�����g�f�B���N�g�����ړ��������ꍇ
"   au BufEnter * execute ":silent! lcd " . escape(expand("%:p:h"), ' ')
" endif

"----------------------------------------
" �e��v���O�C���ݒ�
"----------------------------------------
if has('vim_starting')
   set nocompatible               " Be iMproved

   " Required:
   set runtimepath+=~/.vim/bundle/neobundle.vim/
 endif

 " Required:
 call neobundle#begin(expand('~/.vim/bundle/'))

 " Let NeoBundle manage NeoBundle
 " Required:
 NeoBundleFetch 'Shougo/neobundle.vim'

 " My Bundles here:
 NeoBundle 'Shougo/neocomplcache'
"Note: This option must set it in .vimrc(_vimrc).  NOT IN .gvimrc(_gvimrc)!
" Disable AutoComplPop.
let g:acp_enableAtStartup = 0
" Use neocomplcache.
let g:neocomplcache_enable_at_startup = 1
" Use smartcase.
let g:neocomplcache_enable_smart_case = 1
" Set minimum syntax keyword length.
let g:neocomplcache_min_syntax_length = 3
let g:neocomplcache_lock_buffer_name_pattern = '\*ku\*'

" Enable heavy features.
" Use camel case completion.
"let g:neocomplcache_enable_camel_case_completion = 1
" Use underbar completion.
"let g:neocomplcache_enable_underbar_completion = 1

" Define dictionary.
let g:neocomplcache_dictionary_filetype_lists = {
    \ 'default' : '',
    \ 'vimshell' : $HOME.'/.vimshell_hist',
    \ 'scheme' : $HOME.'/.gosh_completions'
        \ }

" Define keyword.
if !exists('g:neocomplcache_keyword_patterns')
    let g:neocomplcache_keyword_patterns = {}
endif
let g:neocomplcache_keyword_patterns['default'] = '\h\w*'

" Plugin key-mappings.
inoremap <expr><C-g>     neocomplcache#undo_completion()
inoremap <expr><C-l>     neocomplcache#complete_common_string()

" Recommended key-mappings.
" <CR>: close popup and save indent.
inoremap <silent> <CR> <C-r>=<SID>my_cr_function()<CR>
function! s:my_cr_function()
  return neocomplcache#smart_close_popup() . "\<CR>"
  " For no inserting <CR> key.
  "return pumvisible() ? neocomplcache#close_popup() : "\<CR>"
endfunction
" <TAB>: completion.
inoremap <expr><TAB>  pumvisible() ? "\<C-n>" : "\<TAB>"
" <C-h>, <BS>: close popup and delete backword char.
inoremap <expr><C-h> neocomplcache#smart_close_popup()."\<C-h>"
inoremap <expr><BS> neocomplcache#smart_close_popup()."\<C-h>"
inoremap <expr><C-y>  neocomplcache#close_popup()
inoremap <expr><C-e>  neocomplcache#cancel_popup()
" Close popup by <Space>.
"inoremap <expr><Space> pumvisible() ? neocomplcache#close_popup() : "\<Space>"

" For cursor moving in insert mode(Not recommended)
"inoremap <expr><Left>  neocomplcache#close_popup() . "\<Left>"
"inoremap <expr><Right> neocomplcache#close_popup() . "\<Right>"
"inoremap <expr><Up>    neocomplcache#close_popup() . "\<Up>"
"inoremap <expr><Down>  neocomplcache#close_popup() . "\<Down>"
" Or set this.
"let g:neocomplcache_enable_cursor_hold_i = 1
" Or set this.
"let g:neocomplcache_enable_insert_char_pre = 1

" AutoComplPop like behavior.
"let g:neocomplcache_enable_auto_select = 1

" Shell like behavior(not recommended).
"set completeopt+=longest
"let g:neocomplcache_enable_auto_select = 1
"let g:neocomplcache_disable_auto_complete = 1
"inoremap <expr><TAB>  pumvisible() ? "\<Down>" : "\<C-x>\<C-u>"

" Enable omni completion.
autocmd FileType css setlocal omnifunc=csscomplete#CompleteCSS
autocmd FileType html,markdown setlocal omnifunc=htmlcomplete#CompleteTags
autocmd FileType javascript setlocal omnifunc=javascriptcomplete#CompleteJS
autocmd FileType python setlocal omnifunc=pythoncomplete#Complete
autocmd FileType xml setlocal omnifunc=xmlcomplete#CompleteTags

" Enable heavy omni completion.
if !exists('g:neocomplcache_omni_patterns')
  let g:neocomplcache_omni_patterns = {}
endif
let g:neocomplcache_omni_patterns.php = '[^. \t]->\h\w*\|\h\w*::'
let g:neocomplcache_omni_patterns.c = '[^.[:digit:] *\t]\%(\.\|->\)'
let g:neocomplcache_omni_patterns.cpp = '[^.[:digit:] *\t]\%(\.\|->\)\|\h\w*::'

" For perlomni.vim setting.
" https://github.com/c9s/perlomni.vim
let g:neocomplcache_omni_patterns.perl = '\h\w*->\h\w*\|\h\w*::'
 NeoBundle 'Shougo/neosnippet.vim'
" Plugin key-mappings.
imap <C-k>     <Plug>(neosnippet_expand_or_jump)
smap <C-k>     <Plug>(neosnippet_expand_or_jump)
xmap <C-k>     <Plug>(neosnippet_expand_target)

" SuperTab like snippets behavior.
imap <expr><TAB> neosnippet#expandable_or_jumpable() ?
\ "\<Plug>(neosnippet_expand_or_jump)"
\: pumvisible() ? "\<C-n>" : "\<TAB>"
smap <expr><TAB> neosnippet#expandable_or_jumpable() ?
\ "\<Plug>(neosnippet_expand_or_jump)"
\: "\<TAB>"
" For snippet_complete marker.
if has('conceal')
  set conceallevel=2 concealcursor=i
endif
let g:neosnippet#enable_snipmate_compatibility = 1
let g:neosnippet#snippets_directory='~/.vim/**/snip**'

 NeoBundle 'Shougo/neosnippet-snippets'
 NeoBundle 'kien/ctrlp.vim'
 NeoBundle 'tpope/vim-fugitive'
 NeoBundle 'vim-perl/vim-perl'
 NeoBundle 'flazz/vim-colorschemes'
 NeoBundle 'ujihisa/unite-colorscheme'
 NeoBundle 'Shougo/unite.vim'
 let g:unite_source_history_yank_enable = 1
 NeoBundle 'Shougo/vimproc.vim',{
      \ 'build' : {
      \     'windows' : 'make -f make_mingw32.mak',
      \     'cygwin' : 'make -f make_cygwin.mak',
      \     'mac' : 'make -f make_mac.mak',
      \     'unix' : 'make -f make_unix.mak',
      \    },
      \ }
 NeoBundle 'honza/vim-snippets'
 NeoBundle 'Shougo/vimfiler.vim'
 let g:vimfiler_as_default_explorer = 1
 " You can specify revision/branch/tag.
 NeoBundle 'Shougo/vimshell', { 'rev' : '3787e5' }

 call neobundle#end()

 " Required:
 filetype plugin indent on

 " If there are uninstalled bundles found on startup,
 " this will conveniently prompt you to install them.
 NeoBundleCheck

"----------------------------------------
" �ꎞ�ݒ�
"----------------------------------------
