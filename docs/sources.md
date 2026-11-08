# Datasheet и исходные документы

Проверка выполнена для конкретных выбранных компонентов. Физический прототип
пока не изготовлен. Ссылки на зеркала содержат оригинальные документы
производителей, а не распиновку похожего 8051.

| Компонент / вопрос | Документ и использование |
|---|---|
| Siemens SAB80535-N | [Оригинальный Siemens SAB80515/80535](https://www.ardent-tool.com/datasheets/Siemens_SAB80515_80535.pdf): таблица заказа SAB80535-N, корпус P-LCC-68, распиновка, VBB/VPD, активный низкий RESET, внешняя CODE/XDATA, электрические и временные параметры. Документ содержит оба семейства, применены данные именно ROMless SAB80535-N. |
| Панель PLCC-68 | [Каталог Preci-Dip](https://static.chipdip.ru/lib/825/DOC031825282.pdf), печатная стр. 94: серия 540, 540-99-068-24-000-1, корпус 30,22 мм, сетка 2,54 мм, наружный ряд 25,4 мм, внутренний 20,32 мм, рекомендованное отверстие не менее 0,75 мм. На PCB 0,8 мм. Нумерация проверена отдельно от 3D-модели. |
| SST39SF010A | [Microchip DS20005022](https://ww1.microchip.com/downloads/aemDocuments/documents/MPD/ProductDocuments/DataSheets/SST39SF010A-SST39SF020A-SST39SF040-Data-Sheet-DS20005022.pdf): PDIP-32, 5 В, 70 нс, команды программирования, A16 и WE#. |
| AS6C62256A-70PCN | [Alliance Memory](https://www.alliancememory.com/wp-content/uploads/AS6C62256A-70PCN_AS6C62256A.pdf): вариант **A**, PDIP-28, TTL VIH=2,2 В, SRAM 32K×8, чтение и запись 70 нс. Не заменять автоматически на вариант без A. |
| SN74HCT573 | [Texas Instruments](https://www.ti.com/lit/ds/symlink/sn74hct573.pdf): входные TTL-уровни, распиновка защёлки, задержки и времена установки. |
| SN74AHCT125 | [Texas Instruments](https://www.ti.com/lit/ds/symlink/sn74ahct125.pdf): TTL-входы и трёхстабильная развязка UART. |
| FT232RL | [FTDI DS_FT232R](https://ftdichip.cn/Support/Documents/DataSheets/ICs/DS_FT232R.pdf): SSOP-28, VCCIO, CBUS3/PWREN#, bus-powered 500 mA, suspend pull-down. |
| TPS2041B | [Texas Instruments](https://www.ti.com/lit/ds/symlink/tps2041b.pdf): ограничение тока, EN#, OC# и разводка параллельных IN/OUT. |
| MCP120-475 | [Microchip DS11184D](https://ww1.microchip.com/downloads/en/DeviceDoc/11184D.pdf): активный низкий open-drain RESET, порог 4,50…4,75 В и задержка. |
| USBLC6-2SC6 | [STMicroelectronics](https://www.st.com/resource/en/datasheet/usblc6-2.pdf): распиновка SOT23-6 и защита линий USB. |
| HRO TYPE-C-31-M-12 | [Оригинальный механический чертёж HRO, 2020-12-08](https://datasheet.lcsc.com/datasheet/pdf/9e56b777c022540fcce7c7f67825f55e.pdf): контакты, совмещённые площадки, крепёжные пазы, позиционирующие отверстия и край PCB. Изменения относительно стандартной библиотеки описаны в manufacturing.md. |
| ECS-110.5-20-4X | [ECS HC-49USX](https://www.ecsxtal.com/store/pdf/hc-49usx.pdf): THT, шаг 4,88 мм, 11,0592 МГц, CL20 пФ. |
| MF-MSMF075-2 | [Bourns MF-MSMF](https://www.bourns.com/docs/product-datasheets/mf-msmf.pdf): PTC 0,75 А, 1812 и механические допуски. |
| Производство | [JLCPCB capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), проверено 2026-11-08: два слоя, сверление, пазы, текст 1 мм / штрих 0,15 мм, медь и маска. |

Назначение всех 68 выводов сохранено в pinout.md. Расчёт уровней и временной
бюджет находятся в architecture.md, процедура программирования — bring-up.md.
Источники, лицензии и известные отличия сторонних STEP перечислены в models.md.

Имеющиеся у владельца NEC D4365C-12L и SN74LS373N в BOM v1.0 не включены.
Распиновка LS373 отличается от HCT573; по NEC не подтверждён оригинальный
datasheet точного варианта. Подменять его документом D4364 нельзя.
