# Bongo Cat for Omarchy

A little cat that sits in your bar and drums its paws when you type, and on the beat when music plays. Stop for a second and it goes back to chilling, both paws up.

![Bongo cat drumming in the bar](https://github.com/Samon97/omarchy-bongocat/raw/main/assets/bongocat.gif)

## Install

```bash
omarchy plugin add https://github.com/Deoxizn/omarchy-bongocat.git --enable
```

Then turn it on in the bar:

```bash
omarchy plugin enable pizza.dirty.bongocat
```

You also need two small tools for it to work:

```bash
sudo pacman -S evtest cava
```

`evtest` hears your keys. `cava` hears your music. If one is missing, the other side still works.

## First run

The cat needs to read your keyboard. Run this one time:

```bash
sudo ~/.config/omarchy/plugins/pizza.dirty.bongocat/setup/install.sh
```

It adds you to the `input` group and sets up a rule so your keyboard stays readable. Log out and back in once if it does nothing right away.

## Uninstall

```bash
omarchy plugin disable pizza.dirty.bongocat
rm -rf ~/.config/omarchy/plugins/pizza.dirty.bongocat
```
