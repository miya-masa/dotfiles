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
" nnoremap <Leader><C-B> :Rooter<CR>:Buffer<CR>
nnoremap <Leader><C-B> :Rooter<CR>:Telescope buffers<CR>
" Do not remove the trailing blank
" nnoremap <Leader><C-R> :Rooter<CR>:Rg
nnoremap <Leader><C-R> :Telescope live_grep<CR>
nnoremap <Leader><C-L> :Telescope grep_string<CR>
" nnoremap <Leader><C-G> :GFiles<CR>
nnoremap <Leader><C-G> :Telescope git_files<CR>
nnoremap <Leader><C-Q> :Telescope quickfix<CR>
" nnoremap <Leader><C-F> :Files<CR>
" nnoremap <Leader><C-F> :Files<CR>
" nnoremap <leader><C-L> :Line<CR>
" nnoremap <leader><C-L> :Telescope <CR>
" nnoremap <Leader><C-T> :Tags<CR>
nnoremap <Leader>w :w!<CR>
nnoremap <Leader>tsl V:TranslateVisual<CR>
nnoremap <Leader>tsr V:TranslateReplace<CR>
nnoremap - :NvimTreeToggle<CR>
nnoremap <Leader>y :NvimTreeFindFile<CR>
nnoremap <silent> <Leader>sj :SplitjoinJoin<CR>
nnoremap <silent> <Leader>ss :SplitjoinSplit<CR>
" these "Ctrl mappings" work well when Caps Lock is mapped to Ctrl
nnoremap <silent> t<C-n> :cd %:p:h<cr>:TestNearest<CR>
nnoremap <silent> t<C-f> :cd %:p:h<cr>:TestFile<CR>
nnoremap <silent> t<C-s> :cd %:p:h<cr>:TestSuite<CR>
nnoremap <silent> t<C-l> :cd %:p:h<cr>:TestLast<CR>
nnoremap <silent> t<C-g> :cd %:p:h<cr>:TestVisit<CR>
nmap <C-q> <Plug>(quickrun)<CR>
" Do not remove the trailing blank
nnoremap gp<Space> :G push 
nnoremap gp<CR> :G push<CR>
nnoremap gpf<CR> :G push -f<CR>
nnoremap gca<CR> :G commit --amend<CR>
" Do not remove the trailing blank
nnoremap gc<Space> :G commit 


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
