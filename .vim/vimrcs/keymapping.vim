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
nnoremap <Leader><C-B> :Rooter<CR>:Buffer<CR>
nnoremap <Leader><C-R> :Rooter<CR>:Rg<CR>
nnoremap <Leader><C-G> :GFiles<CR>
nnoremap <Leader><C-F> :Files<CR>
nnoremap <leader><C-L> :Line<CR>
nnoremap <Leader><C-T> :Tags<CR>
nnoremap <Leader>w :w!<CR>
nnoremap <Leader>tsl V:TranslateVisual<CR>
nnoremap <Leader>tsr V:TranslateReplace<CR>
" nnoremap - :NERDTreeToggle<CR>
nnoremap - :CocCommand explorer<CR>
" nnoremap <Leader>y :call CocAction('runCommand', 'explorer.doAction', 'closest', ['reveal:0'], [['relative', 0, 'file']])<CR>
" nnoremap <Leader>y :NERDTreeFind<CR>
nmap <Leader>gx <Plug>(openbrowser-smart-search)
" these "Ctrl mappings" work well when Caps Lock is mapped to Ctrl
nmap <silent> t<C-n> :cd %:p:h<cr>:TestNearest<CR>
nmap <silent> t<C-f> :cd %:p:h<cr>:TestFile<CR>
nmap <silent> t<C-s> :cd %:p:h<cr>:TestSuite<CR>
nmap <silent> t<C-l> :cd %:p:h<cr>:TestLast<CR>
nmap <silent> t<C-g> :cd %:p:h<cr>:TestVisit<CR>
" }}}

" Terminal Mode {{{
tnoremap <silent> <leader><C-[> <C-\><C-n>
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

" Mapping {{{
map <Leader>cc <Plug>(operator-camelize)
map <Leader>C <Plug>(operator-decamelize)
" }}}
