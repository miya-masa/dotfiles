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
nnoremap <Leader><S-\> :vertical<CR>
nnoremap <Leader>- :split<CR>
nnoremap <silet> <C-q> :QuickRun -outputter message<CR>
nnoremap <Leader><C-B> :Buffer<CR>
nnoremap <Leader><C-R> :Rg<Space>
nnoremap <Leader><C-G> :GFiles<CR>
nnoremap <leader><C-L> :Line<CR>
nnoremap <Leader><C-T> :Tags<CR>
nnoremap <Space><CR> V:!sh<CR>
nnoremap <Leader>tsl V:TranslateVisual<CR>
nnoremap <Leader>tslr V:TranslateReplace<CR>
nnoremap - :NERDTreeToggle<CR>
nnoremap <Leader>y :NERDTreeFind<CR>

nmap <silent> <Leader>ig <Plug>IndentGuidesToggle
nmap <silent> <Leader>ie <Plug>IndentGuidesEnable
nmap <silent> <Leader>id <Plug>IndentGuidesDisable
nmap <silent> <Leader>w :w!<CR>
" }}}

" Terminal Mode {{{
tnoremap <silent> <leader><C-[> <C-\><C-n>
" }}}

" Insert Mode {{{
inoremap <silent> jj <ESC>
" }}}

" Visual Mode {{{
vnoremap <Space><CR> :!sh<CR>
vnoremap <Leader>tsl :TranslateVisual<CR>
vnoremap <Leader>tslr :TranslateReplace<CR>
" Start interactive EasyAlign in visual mode (e.g. vip<Enter>)
vmap <Enter> <Plug>(EasyAlign)
" }}}
