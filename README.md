# dotfiles

## USAGE

### install and deploy

```bash
apt update && apt install -y curl sudo git
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply miya-masa
```

## daily operations

```ash
chezmoi update
chezmoi apply
```
