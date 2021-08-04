## Idea
Entry:
- 3MA cross (200, 50, 9)
- buy if price < fastMA

Exit:
- trail stop n x ATR 
- trail stop at slowMA
- TP n x ATR above fastMA


# To Do
+ entry to true cross (not if already crossed)
only enter after cross or if emaFast & emaMid difference < 0.5 ATR

+ reverse MA cross - exit & cancel all orders if crossed in opposite direction & price > emaFast (if long)

+ entry if ADX > 25 only

- order increase if stopped out WITHOUT profit (not if trail stop hit with profit)