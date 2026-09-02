# Note to NexTuxLinq author

Suggested GitHub issue title:

**Related work: Phanteks LCD6-HD Linux control**

Suggested message:

> Hi — I wanted to thank you for NexTuxLinq and share some related work it helped inspire.
>
> We have been reverse-engineering native Linux control for the **Phanteks LCD6-HD**. It is a different device from the Matrix900, so the packet format and commands are not directly compatible, but your protocol notes strongly influenced how we approached the investigation: capture known-good Windows traffic, verify acknowledgements, change one variable at a time, and avoid guessing at firmware/reset behavior.
>
> That approach paid off. We now have **native Linux static-image control working** on the LCD6-HD. The confirmed transaction is:
>
> `0x2A config -> acknowledged 0x28 JPEG transfer -> 0x30 activation`
>
> The final breakthrough was finding that the successful activation packet begins:
>
> `01 30 00 01 00 01 ...`
>
> rather than the `...00 00` form we had initially reconstructed. After updating the LCD from firmware `V1.0.0.0` to `V1.0.0.10` through the official software and correcting that activation byte, Ubuntu successfully took over the display.
>
> Source and protocol notes:
> https://github.com/klandstudio/Linux/tree/main/projects/phanteks-lcd6-linux
>
> Project write-up:
> https://klandstudio.net/labs/phanteks-lcd6-linux/
>
> We credited NexTuxLinq as an important methodological reference. Thanks for putting your work out there — it genuinely helped.
