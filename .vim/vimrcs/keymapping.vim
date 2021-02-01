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
nnoremap <Leader><C-B> :Buffer<CR>
nnoremap <Leader><C-R> :Rg<Space>
nnoremap <Leader><C-G> :GFiles<CR>
nnoremap <Leader><C-F> :Files<CR>
nnoremap <leader><C-L> :Line<CR>
nnoremap <Leader><C-T> :Tags<CR>
nnoremap <Leader>w :w!<CR>
nnoremap <Leader>tsl V:TranslateVisual<CR>
nnoremap <Leader>tsr V:TranslateReplace<CR>
nnoremap - :NERDTreeToggle<CR>
nnoremap <Leader>y :NERDTreeFind<CR>
nmap <Leader>gx <Plug>(openbrowser-smart-search)

" }}}

" Terminal Mode {{{
tnoremap <silent> <leader><C-[> <C-\><C-n>
" }}}

" Insert Mode {{{
inoremap <silent> jj <ESC>
inoremap <C-H> <BS>
" }}}

" Visual Mode {{{
vnoremap <Leader>tsl :TranslateVisual<CR>
vnoremap <Leader>tsr :TranslateReplace<CR>
" Start interactive EasyAlign in visual mode (e.g. vip<Enter>)
vmap <Enter> <Plug>(EasyAlign)
vmap <Leader>gx <Plug>(openbrowser-smart-search)
" }}}

" Commandline Mode {{{
cnoremap <C-H> <BS>
cnoremap <C-F> <Right>
cnoremap <C-B> <Left>
" }}}
