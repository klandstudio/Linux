# Acknowledgements

## NexTuxLinq / anoraknophobia

[NexTuxLinq](https://github.com/anoraknophobia/NexTuxLinq) by **anoraknophobia** was an important methodological reference for this project.

The Matrix900 work in NexTuxLinq is **not** protocol-compatible with the LCD6-HD, and this repository does not claim that its command bytes or packet formats were copied from that project. Its value was in demonstrating a disciplined approach to undocumented Phanteks USB devices:

- capture traffic from the official Windows software;
- identify request/response boundaries rather than guessing from isolated bytes;
- verify acknowledgements before advancing;
- change one variable at a time;
- avoid speculative reset, bootloader, or firmware commands;
- document what is observed separately from what is inferred.

That approach materially influenced the LCD6-HD investigation and helped keep the reverse-engineering work evidence-driven.

## Phanteks

Device names, NexLinq, and related trademarks belong to Phanteks and their respective owners. This is an independent interoperability/research project and is not affiliated with or endorsed by Phanteks.

## Human testing + AI-assisted analysis

The protocol work was developed through hands-on testing on real hardware, USB packet captures, inspection of the official software behavior, and AI-assisted analysis/code iteration. Claims marked as confirmed in this repository were tied back to observed device behavior rather than treated as proven solely because code or static analysis suggested them.
