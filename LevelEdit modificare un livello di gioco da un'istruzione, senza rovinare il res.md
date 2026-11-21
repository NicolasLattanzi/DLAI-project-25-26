# LevelEdit: modificare un livello di gioco da un'istruzione, senza rovinare il resto

Nov 19, 2026 · @Flavio

## 1. In breve

LevelEdit è un modello che riceve l'immagine di un livello di gioco e un'istruzione in linguaggio naturale, e restituisce il livello modificato. Deve fare tre cose insieme: **eseguire** ciò che è chiesto, **conservare** tutto il resto e **lasciare il livello giocabile**.

**Esempio.** Input: l'immagine di un dungeon e l'istruzione *"Move the key behind the door and add a bridge over the water"*. Output: lo stesso dungeon con la chiave spostata e il ponte aggiunto. Nient'altro cambia e le scale d'uscita restano raggiungibili.

**Perché è interessante.** È l'equivalente di un editor di immagini guidato da istruzioni, come InstructPix2Pix, ma con una differenza decisiva: qui ogni risultato si **verifica con un programma**. Si controlla se l'istruzione è soddisfatta, quante celle sono cambiate senza motivo e se il livello è ancora completabile.

**Le scelte principali, in una riga ciascuna:**

- **Stile del gioco:** dungeon visti dall'alto, ispirati a *Link's Awakening*, con meccaniche ridotte all'essenziale.
- **Rappresentazione:** il livello è una griglia di celle; l'immagine è il suo rendering.
- **Dati di addestramento:** generati interamente da noi, con un generatore e un verificatore automatico per ogni istruzione.
- **Test su livelli reali:** stanze dello Zelda originale per NES (dal Video Game Level Corpus) e di Link's Awakening (estratte dalla nostra copia con un emulatore).
- **Modello principale (M1):** una rete che "ridisegna" il livello cella per cella, imparando a non toccare il resto e a mantenerlo giocabile.

**I tre contributi:**

1. **Un benchmark** di modifiche a livelli, con verificatori automatici e split che misurano la generalizzazione.
2. **Un editor a griglia (M1)** con una testa "cambia sì/no" e una loss differenziabile di raggiungibilità, più una versione iterativa (M1-iter) per le istruzioni ambigue.
3. **Un confronto** con modelli molto più grandi (LLM e VLM) e con un modello che scrive comandi invece di ridisegnare (M2).

**Aree del corso coperte:** gaming and AI, multimodal learning (immagine + testo), image generation (in forma discreta), program synthesis (M2), reasoning.

## 2. Concetti di base

Questi termini tornano in tutto il documento. Conviene leggerli una volta prima del resto.

| Termine | Significato in questo progetto |
| --- | --- |
| **Cella** | Un quadrato della griglia del livello. Il nostro livello ha 16 righe × 20 colonne = 320 celle |
| **Tile** | Il contenuto di una cella: muro, pavimento, acqua, chiave… (11 tipi in tutto) |
| **Griglia** | Il livello come matrice 16 × 20 di codici di tile. È la rappresentazione "vera" del livello |
| **Rendering** | La trasformazione della griglia in immagine: ogni cella diventa un quadrato di 14 × 14 pixel con la grafica del suo tile |
| **Istruzione** | La richiesta in inglese, es. *"Move the key next to the stairs"* |
| **Operazione** | Una modifica elementare con parametri precisi, es. `MOVE(chiave, accanto, scale)` |
| **Maschera** | L'insieme delle celle che un'operazione ha il diritto di cambiare. Tutto ciò che è fuori dalla maschera deve restare identico |
| **Verificatore** | Una funzione Python che, dato il livello prima, l'istruzione e il livello dopo, risponde "istruzione soddisfatta" sì o no |
| **BFS** | Visita in ampiezza (*breadth-first search*): l'algoritmo che controlla quali celle il giocatore può raggiungere |
| **Livello valido** | Un livello che rispetta tutte le regole del mondo, compresa la raggiungibilità dell'uscita |
| **Encoder** | La parte di una rete che trasforma un input (immagine o testo) in vettori numerici |
| **ViT / DINOv2** | Un *Vision Transformer* taglia l'immagine in quadratini (patch) e produce un vettore per ognuno. DINOv2 è un ViT già addestrato su milioni di immagini |
| **Token** | Un vettore che rappresenta un pezzo dell'input: una cella dell'immagine o una parola dell'istruzione |
| **Cross-attention** | Il meccanismo con cui ogni cella "guarda" le parole dell'istruzione per capire cosa la riguarda |
| **Self-attention** | Il meccanismo con cui ogni cella "guarda" tutte le altre celle: dà al modello una visione globale del livello |
| **Testa** | Uno strato finale che produce un'uscita specifica (es. "questa cella cambia?") |
| **Loss** | La funzione che misura quanto il modello sbaglia; l'addestramento la minimizza |
| **Congelato** | Un componente pre-addestrato i cui pesi non vengono modificati durante il nostro addestramento |
| **LoRA** | Un modo economico di adattare un modello grande: si addestrano solo piccole matrici aggiuntive |
| **Zero-shot** | Usare un modello così com'è, senza addestrarlo sul nostro compito |
| **Split** | Una partizione dei dati (train, validazione, test). Gli split di test sono costruiti per misurare tipi diversi di generalizzazione |
| **Ablation** | Un esperimento in cui si toglie un componente per misurare quanto contava |

## 3. Domanda di ricerca e ipotesi

**Domanda principale.** Un modello piccolo e addestrato su livelli sintetici riesce a modificare un livello da un'istruzione rispettando insieme esecuzione, conservazione e validità? E generalizza a istruzioni composte, formulate da persone, con grafica nuova e su livelli reali?

**Domande secondarie:**

1. Separare *quali celle cambiano* da *in cosa cambiano* riduce le modifiche non richieste?
2. Un vincolo esplicito di raggiungibilità rende i livelli più spesso giocabili?
3. Quando un'istruzione ha più risposte giuste, una decodifica iterativa evita risultati incoerenti (per esempio "mezzo ponte qui e mezzo là")?
4. Un modello specializzato da circa 15M parametri regge il confronto con un VLM generico da 2 miliardi adattato con LoRA?

**Ipotesi.** Le scriviamo prima degli esperimenti e le fissiamo nel repository con la data. Ogni risultato le conferma o le smentisce; una smentita ben spiegata vale quanto una conferma.

| # | Ipotesi | Come la verifichiamo |
| --- | --- | --- |
| H1 | La testa "cambia sì/no" riduce le modifiche non richieste rispetto a una testa unica | M1 contro M1 senza testa di modifica, a parità di tutto il resto |
| H2 | La loss di raggiungibilità aumenta i livelli validi, soprattutto sulle istruzioni composte | M1 con λ = 0 contro λ > 0, sugli split composizionale e lunghezza |
| H3 | Sulle istruzioni ambigue M1-iter produce più risultati coerenti di M1 | Confronto sul dataset "ambiguo", dove il ground truth è una tra più soluzioni valide |
| H4 | Un modello che vede solo le celle vicine (CNN) fallisce sui vincoli globali | M1 contro una variante U-Net della stessa taglia |
| H5 | Un encoder visivo pre-addestrato (DINOv2) generalizza meglio a grafica mai vista | DINOv2 contro ViT da zero, sullo split "tileset nuovo" |
| H6 | M1 si avvicina a un VLM da 2B con LoRA, con circa 100 volte meno parametri | M1 contro B4 su tutti gli split |

## 4. Il mondo di gioco

Il mondo è una griglia di 16 righe × 20 colonne con 11 tipi di tile. È abbastanza ricco da somigliare a uno Zelda e abbastanza semplice da essere verificato esattamente.

### 4.1 La griglia

- **Dimensione fissa: 16 × 20.** Corrisponde a 2 × 2 schermate di Link's Awakening, dove ogni schermata è di 8 × 10 tile.
- **Livelli più piccoli** (una stanza di Link's Awakening da 8 × 10, una stanza dello Zelda NES da 11 × 16) si mettono in alto a sinistra. Il resto si riempie con il tile "fuori mappa".
- Coordinate: (riga, colonna), con (0, 0) in alto a sinistra.

### 4.2 I tipi di tile

| Codice | Tile | Simbolo ASCII | Attraversabile | Note |
| --- | --- | --- | --- | --- |
| 0 | Fuori mappa | ` ` | No | Solo riempimento, mai modificato |
| 1 | Muro | `#` | No | Include alberi, rocce e case nei livelli all'aperto |
| 2 | Pavimento | `.` | Sì | Include erba e sentieri |
| 3 | Acqua | `~` | No | Include buche e lava |
| 4 | Ponte | `=` | Sì | Sta dove prima c'era acqua |
| 5 | Porta chiusa | `D` | Solo consumando una chiave |  |
| 6 | Chiave | `K` | Sì | Raccolta passandoci sopra |
| 7 | Blocco | `B` | No | Ostacolo rimovibile o spostabile solo dalle operazioni |
| 8 | Scale (uscita) | `E` | Sì | L'obiettivo del livello |
| 9 | Giocatore | `P` | Sì | Posizione di partenza |
| 10 | Nemico | `M` | No | Il giocatore lo deve aggirare |

### 4.3 Le regole di validità

Un livello è **valido** se rispetta tutte queste regole. Ognuna è una funzione Python con test unitari.

1. **Un solo giocatore** e **almeno una scala** d'uscita.
2. **Bordi chiusi:** le celle sul contorno del livello sono muro o fuori mappa.
3. **Al massimo 2 porte chiuse.** Il numero di chiavi è almeno pari al numero di porte che servono per arrivare all'uscita.
4. **Uscita raggiungibile:** esiste un percorso dal giocatore a una scala, muovendosi nelle 4 direzioni e raccogliendo chiavi per aprire le porte.

**Perché al massimo 2 porte.** Con chiavi tutte uguali e molte porte, decidere se un dungeon è risolvibile diventa un problema computazionalmente difficile: Zelda con chiavi, porte e sporgenze è NP-difficile ([fonte](https://arxiv.org/pdf/2203.17167)). Con al massimo 2 porte il verificatore prova tutti gli ordini di apertura (al massimo 2) ed è esatto e istantaneo.

**Come funziona il controllo di raggiungibilità:**

1. BFS dal giocatore, trattando le porte come muri, raccogliendo le chiavi incontrate.
2. Se l'uscita è raggiunta, il livello è valido.
3. Altrimenti, se ci sono chiavi raccolte e una porta confina con la zona raggiunta, si apre la porta e si ripete dal punto 1. Con 2 porte si provano entrambi gli ordini.

### 4.4 Le relazioni spaziali

Le istruzioni parlano di posizioni relative. Ogni relazione ha una **definizione formale**, così il verificatore è senza ambiguità.

| Relazione (in inglese nelle istruzioni) | Definizione |
| --- | --- |
| *left of / right of / above / below X* | La cella adiacente a X in quella direzione |
| *next to X* | Una qualsiasi delle 4 celle adiacenti a X |
| *behind the door* | Le celle raggiungibili dal giocatore solo passando da quella porta |
| *in front of the door* | Le celle raggiungibili senza passare dalla porta, adiacenti a essa |
| *in the top-left room* (e le altre 3) | Il quadrante 8 × 10 corrispondente della griglia |
| *over the water* (per un ponte) | Un segmento di celle d'acqua in linea retta che collega due zone di pavimento separate |
| *the key / the enemy nearest to X* | Se ci sono più oggetti dello stesso tipo, quello a distanza di Manhattan minore da X |

## 5. Le modifiche e le istruzioni

Ogni istruzione corrisponde a un piccolo programma di 1–3 operazioni. Ogni operazione sa eseguirsi, verificarsi e dire quali celle può toccare.

### 5.1 Le quattro operazioni

| Operazione | Esempio di istruzione | Maschera (celle che possono cambiare) |
| --- | --- | --- |
| `MOVE(oggetto, relazione, riferimento)` | *Move the key behind the door* | La cella di partenza e quella di arrivo |
| `ADD(oggetto, relazione, riferimento)` | *Add a bridge over the water*, *Add an enemy next to the stairs* | Le celle dove compare l'oggetto |
| `REMOVE(oggetto)` | *Remove the enemy nearest to the player* | La cella dell'oggetto |
| `REPLACE(tile_a, tile_b, zona)` | *Turn the water in the top-left room into floor* | Le celle di tipo tile\_a dentro la zona |

**Oggetti ammessi:** chiave, blocco, nemico, scale, porta chiusa, ponte (solo con `ADD`), giocatore (solo con `MOVE`).

### 5.2 Le tre parti di ogni operazione

1. **Precondizione:** l'operazione ha senso su questo livello? Esempio: `MOVE(chiave, ...)` richiede che esista una chiave; la cella di arrivo deve essere pavimento.
2. **Esecutore:** applica la modifica alla griglia e restituisce la nuova griglia e la maschera.
3. **Verificatore:** controlla su una griglia *qualsiasi* che l'effetto richiesto ci sia. Esempio: per `MOVE(chiave, behind, porta)` controlla che una chiave stia nella zona "dietro la porta" e che quella vecchia non ci sia più.

Il verificatore non confronta con un'unica risposta giusta: accetta **ogni** soluzione corretta. Questo rende la valutazione onesta anche quando le soluzioni possibili sono più d'una.

### 5.3 Istruzioni composte

- Da 1 a 3 operazioni, unite da *and* o *then* (es. *"Remove the block and move the key next to the stairs"*).
- Si applicano in ordine. La maschera totale è l'unione delle maschere.
- Il livello finale deve essere **valido**: il generatore scarta le combinazioni che lo rompono.

### 5.4 Il problema delle risposte multiple

Molte istruzioni ammettono più soluzioni corrette ("un ponte sull'acqua" può stare in più punti). Gestiamo la cosa con **due versioni del dataset**:

| Versione | Ground truth per l'addestramento | Scopo |
| --- | --- | --- |
| **Canonica** | Scelta con una regola fissa: la soluzione più vicina al riferimento; a parità, riga più piccola, poi colonna più piccola | Versione principale: ogni esempio ha una sola risposta |
| **Ambigua** | Una soluzione valida scelta a caso | Studiare la "media" tra risposte e il vantaggio di M1-iter (ipotesi H3) |

In entrambe le versioni la valutazione usa i verificatori, quindi ogni soluzione valida è considerata corretta.

### 5.5 Il linguaggio delle istruzioni

Le istruzioni sono in **inglese**, perché gli encoder di testo pre-addestrati funzionano meglio in inglese.

1. **Template:** 5–10 frasi per operazione e relazione, con sinonimi (*move/put/place*, *next to/beside*).
2. **Riformulazioni:** un LLM open riscrive offline circa il 30% delle istruzioni di train. Un secondo passaggio dell'LLM controlla che il significato non sia cambiato. Controlliamo a mano un campione di 200 riformulazioni e scartiamo i tipi di errore ricorrenti.
3. **Test umano:** circa 300 istruzioni scritte da noi, senza guardare i template, mai usate in addestramento. Ognuna viene associata a mano all'operazione corrispondente, così il verificatore funziona anche qui.

## 6. Generatore e dataset

Tutti i dati di addestramento sono generati da noi: circa 200.000 esempi, prodotti in pochi minuti. Ogni esempio ha immagine e griglia prima e dopo, istruzione, maschera, programma e proprietà del livello.

### 6.1 Il generatore di livelli

Il generatore produce livelli validi di tre forme, in proporzioni simili:

| Forma | Dimensione | Ispirazione |
| --- | --- | --- |
| Stanza singola | 8 × 10 | Una schermata di Link's Awakening |
| Stanza larga | 11 × 16 | Una stanza dello Zelda NES |
| Mini-dungeon | 16 × 20 (2 × 2 stanze collegate da varchi) | Un pezzo di dungeon di Link's Awakening |

**I passi del generatore:**

1. **Struttura:** muri sul contorno; per i mini-dungeon, muri tra le 4 stanze con 1–2 varchi ciascuno.
2. **Interni:** muri interni con *random walk* o con piccoli modelli di stanza (colonne, corridoi, isole).
3. **Acqua:** con una certa probabilità, un fiume o una pozza che divide una stanza in due zone, eventualmente già attraversato da un ponte.
4. **Porte e chiavi:** con una certa probabilità, 1–2 porte chiuse in un varco, con le chiavi corrispondenti posizionate in zone raggiungibili prima della porta.
5. **Oggetti:** giocatore, scale, 0–4 nemici, 0–3 blocchi.
6. **Controllo:** si applicano le regole di validità (sezione 4.3) e si scartano i livelli che non le rispettano.

I parametri (densità dei muri, probabilità di acqua e porte, numero di oggetti) si scelgono a caso per ogni livello, così il dataset è vario.

Una base già pronta da cui partire, se utile, è [MiniGrid](https://minigrid.farama.org/): ha già muri, porte chiuse, chiavi, lava e rendering in immagine. Il generatore resta comunque nostro, scritto in numpy.

### 6.2 Come nasce un esempio

1. Si genera un livello valido.
2. Si scelgono a caso 1–3 operazioni le cui precondizioni sono soddisfatte.
3. Si eseguono: si ottengono il livello finale e la maschera.
4. Si controlla che il livello finale sia valido; altrimenti si ricomincia dal punto 2.
5. Si produce l'istruzione (template, eventualmente riformulato).
6. Si fanno i rendering del livello iniziale e di quello finale.
7. Si salva tutto.

### 6.3 Il rendering

- **14 × 14 pixel per cella**, quindi immagini da 280 × 224 pixel. Il 14 non è casuale: è la dimensione delle patch di DINOv2, così **ogni cella diventa esattamente un token**.
- **Grafica:** tileset gratuiti CC0 in stile retrò (almeno 4 per l'addestramento, 1 tenuto da parte solo per il test).
- **Variazione:** piccole variazioni casuali di colore e luminosità, per non far imparare al modello un tileset preciso.

### 6.4 Cosa salviamo per ogni esempio

| Campo | Formato |
| --- | --- |
| Griglia iniziale e finale | Matrici 16 × 20 di interi (0–10) |
| Immagine iniziale e finale | PNG 280 × 224 |
| Istruzione | Stringa in inglese, più un flag "template / riformulata / umana" |
| Programma | Lista di operazioni con parametri, es. `MOVE K (3,4) -> (10,12)` |
| Maschera | Matrice 16 × 20 di 0/1 |
| Proprietà | Validità, raggiungibilità, numero di oggetti, zone, prima e dopo |
| Metadati | Seed, forma del livello, tileset usato, versione canonica o ambigua |

### 6.5 Gli split

Ogni split di test misura un tipo diverso di generalizzazione. L'idea viene da gSCAN, il benchmark di riferimento per istruzioni in un mondo a griglia, che valuta otto tipi di generalizzazione composizionale e mostra che i modelli standard falliscono quando servono regole composizionali sistematiche ([fonte](https://par.nsf.gov//servlets/purl/10217557)).

| Split | Dimensione | Cosa contiene | Cosa misura |
| --- | --- | --- | --- |
| Train | \~200.000 | 1–2 operazioni, tileset di train |  |
| Validazione | 10.000 | Come il train | Scelta degli iperparametri, early stopping |
| Test IID | 2.000 | Come il train, livelli nuovi | Prestazione base |
| Test composizionale | 2.000 | Coppie operazione-relazione escluse dal train (es. `MOVE` + *behind* e `ADD` + *in the top-right room*) | Composizione di cose note in modi nuovi |
| Test lunghezza | 2.000 | 3 operazioni | Istruzioni più lunghe del train |
| Test tileset nuovo | 2.000 | Grafica mai vista | Percezione |
| Test umano | \~300 | Istruzioni scritte a mano | Linguaggio vero |
| Test ambiguo | 2.000 | Versione ambigua (sezione 5.4) | Coerenza con risposte multiple |
| Test livelli reali | Alcune centinaia | Stanze di Zelda NES e Link's Awakening (sezione 7) | Dal sintetico al reale |

Le esclusioni del test composizionale si applicano anche alle riformulazioni: una coppia esclusa non compare mai in train, in nessuna forma.

## 7. Livelli reali per il test

Il modello si addestra solo su livelli sintetici e si testa anche su stanze vere di due giochi. È il test più convincente del progetto: dal sintetico al reale.

### 7.1 L'idea chiave: modifiche automatiche anche sui livelli reali

Le nostre operazioni funzionano su **qualsiasi** griglia. Quindi su una stanza vera:

1. la si converte nelle nostre 11 categorie di tile;
2. si aggiungono giocatore, chiave o scale se mancano, nelle posizioni che rendono la stanza valida;
3. si applica un'operazione con l'esecutore;
4. si ottengono gratis il livello modificato corretto, la maschera e il verificatore.

Così abbiamo un test set di modifiche su livelli veri senza annotare nulla a mano.

### 7.2 Zelda per NES (1986), dal VGLC

- **Fonte:** il [Video Game Level Corpus](https://www.github.com/TheVGLC/TheVGLC), che contiene i dungeon della prima quest in file di testo.
- **Quante stanze:** il progetto del corso sulle NCA ne ha estratte 236 dai 9 dungeon, di cui 136 diverse tra loro ([progetto](https://github.com/NicoPozio/zelda-nca)). Possiamo riusarne il parser.
- **Formato:** stanze da 11 × 16 tile, che mettiamo nella nostra griglia 16 × 20 con il riempimento "fuori mappa".
- **Conversione:** i caratteri del VGLC (muro, pavimento, blocco, porta, scale, nemico, acqua/lava, vuoto) si mappano sulle nostre categorie con una tabella.
- **Limite noto:** il VGLC non annota i muri distruttibili, come segnala lo stesso progetto del corso.
- **Costo:** quasi nullo. È il primo test reale da fare.

### 7.3 Link's Awakening (Game Boy, 1993), dalla nostra copia

Il gioco ha tre mappe da 16 × 16 schermate: l'overworld e due mappe sotterranee con dungeon e grotte ([fonte](https://zeldaspeedruns.com/la/doghouse/in-game-maps)). Ogni schermata è di 8 × 10 tile.

**Strumento principale: [PyBoy](https://docs.pyboy.dk/)**, un emulatore Game Boy scritto in Python, installabile con `pip install pyboy`. Funziona con il dump della versione originale e dà accesso diretto alla memoria e alla mappa dei tile dello sfondo ([API](https://docs.pyboy.dk/api/tilemap.html)).

**Procedura di estrazione:**

1. Si carica la ROM e un salvataggio all'inizio di un dungeon.
2. Si raggiunge ogni stanza camminando, oppure scrivendo nella RAM i byte che indicano la destinazione della prossima transizione (overworld, dungeon o area laterale, più il numero di stanza; [RAM map](<https://datacrystal.tcrf.net/wiki/The_Legend_of_Zelda:_Link%27s_Awakening_(Game_Boy)/RAM_map>)).
3. Si leggono i 20 × 16 tile da 8 pixel visibili e si raggruppano 2 × 2 negli 8 × 10 tile veri della stanza.
4. Ogni ID di tile si converte in una delle nostre categorie con una **tabella costruita una volta sola a mano**: muro, pavimento, buca/acqua, porta, blocco, scale e così via.
5. I nemici si leggono dall'API degli sprite.

**Ordine di lavoro:** prima le stanze dei dungeon, che somigliano di più al nostro mondo; poi, se resta tempo, le schermate all'aperto (alberi, rocce e case diventano muro; erba e sentieri pavimento; i cespugli blocco).

**Alternativa:** il randomizer [LADXR](https://git.hollymcfarland.com/monorail/Archipelago/src/commit/43874b1d28fa8d5a5bdc96d4408e303f57763ddd/worlds/ladx/LADXR), scritto in Python, legge le stanze direttamente dalla ROM senza emulazione. Richiede però la ROM inglese v1.0 della versione DX a colori, non l'originale del 1993.

### 7.4 Copyright

- Usiamo il dump della nostra copia solo per un test privato di ricerca. Non siamo avvocati: è il caso più difendibile, non una garanzia.
- **Non pubblichiamo** né la ROM, né le stanze estratte, né la grafica dei giochi. Nel report riportiamo i numeri; eventuali esempi visivi solo con la nostra grafica CC0 e in numero minimo.
- Il dataset pubblicato resta quello sintetico, più il codice per ricostruire i test dal VGLC.

## 8. I modelli

Tutti i modelli ricevono il livello e l'istruzione e producono una griglia finale 16 × 20. Cambia il modo in cui ci arrivano: ridisegnando le celle (M1, M1-iter), scrivendo comandi (M2), oppure usando modelli generici (baseline).

### 8.1 Panoramica

| Modello | Input | Output | Si addestra | Ruolo |
| --- | --- | --- | --- | --- |
| B0 | Griglia | La stessa griglia | No | Pavimento: zero modifiche, zero successi |
| B1 | Griglia + istruzione | Griglia | No | Regole scritte a mano: tetto sulle istruzioni da template |
| B2-testo | Testo: griglia ASCII + istruzione | Testo: griglia ASCII | No | LLM generico (Qwen3 da 1,7B) |
| B2-VLM | Immagine + istruzione | Testo: griglia ASCII | No | VLM generico (Qwen3.5 da 2B) |
| B3 | Immagine + istruzione | Immagine, riconvertita in griglia | No | Editor di immagini (InstructPix2Pix) |
| B4 | Immagine + istruzione | Testo: griglia ASCII | Sì (LoRA) | Baseline forte: VLM adattato al compito |
| **M1** | Immagine + istruzione | Per cella: tile attuale, cambia sì/no, nuovo tile | **Sì** | **Modello principale** |
| **M1-iter** | Immagine + istruzione | Come M1, con raffinamento iterativo | **Sì** | Variante per le istruzioni ambigue |
| M2 | Immagine + istruzione | Sequenza di operazioni, eseguita da un interprete | Sì | Confronto "ridisegnare contro scrivere comandi" |

### 8.2 M1, il modello principale

M1 è una sola rete, addestrata tutta insieme, con quattro blocchi: un encoder visivo, un encoder di testo, un corpo che li unisce e tre teste d'uscita.

&#91;embedded content: architettura di M1 · 2 encoder congelati, corpo addestrato, 3 teste\]

Si addestrano solo il corpo e le tre teste; i due encoder restano congelati. Le metriche si calcolano sulla griglia finale, il renderer serve solo a mostrarla.

**Encoder visivo: DINOv2 ViT-S/14, congelato.**

- È un ViT piccolo (21M parametri, vettori da 384 dimensioni) già addestrato da Meta su 142 milioni di immagini ([model card](https://huggingface.co/spaces/multimodalart/InstantID-FaceID-6M/blob/2bf7ead51a0a9f924abc62b7bb20b154e28ae436/torchhub/facebookresearch_dinov2_main/MODEL_CARD.md)).
- Usa patch da 14 pixel e accetta immagini con lati multipli di 14. L'immagine 280 × 224 produce 20 × 16 = **320 token, uno per cella**. Scartiamo il token di classe.
- Ablation: sbloccare gli ultimi 2 blocchi (learning rate basso) e sostituirlo con un ViT addestrato da zero (ipotesi H5).

**Encoder di testo: l'encoder di Flan-T5-base, congelato.**

- Produce un vettore da 768 dimensioni per ogni token dell'istruzione (massimo 48 token).
- Usiamo **tutti i token**, non la media: parole come *behind* o *left* devono restare visibili una per una.
- Una proiezione lineare porta i vettori da 768 a 384 dimensioni.

**Corpo: 6 blocchi transformer, dimensione 384, 6 teste di attenzione.** In ogni blocco, in ordine:

1. **Self-attention tra le 320 celle:** ogni cella guarda tutte le altre. È la visione globale che serve per i vincoli di raggiungibilità.
2. **Cross-attention dalle celle alle parole:** ogni cella guarda l'istruzione e capisce se la riguarda.
3. **MLP** (strato nascosto 4 × 384), con LayerNorm prima di ogni parte e connessioni residue.

Ai token delle celle si aggiunge un embedding appreso di riga e di colonna, così il modello sa dove si trova ogni cella. Parametri addestrabili: circa 15M.

**Tre teste, applicate a ogni cella:**

| Testa | Uscita | A cosa serve |
| --- | --- | --- |
| Percezione | 11 probabilità (che tile c'è ora) | Riconoscere il livello dall'immagine |
| Modifica | 1 probabilità (questa cella cambia?) | Decidere *dove* intervenire |
| Nuovo tile | 11 probabilità (in cosa cambia) | Decidere *cosa* mettere |

**Come si costruisce la griglia finale.** Per ogni cella: se la probabilità di modifica è sotto 0,5 si tiene il tile riconosciuto dalla percezione; altrimenti si mette il nuovo tile più probabile. Un renderer trasforma poi la griglia in immagine, solo per mostrarla.

### 8.3 M1-iter, per le istruzioni ambigue

**Il problema.** Se un ponte può andare in tre punti, una rete che decide ogni cella indipendentemente distribuisce la probabilità su tutti e tre e produce un ponte spezzato. È lo stesso fenomeno del progetto del corso sulla colorizzazione: con risposte ambigue il modello fa la media delle risposte plausibili ([progetto](https://github.com/solazzo1911897-collab/colorization-mean-vs-mode)).

**La soluzione: decodifica iterativa in stile MaskGIT** ([paper](https://arxiv.org/pdf/2202.04200)). Il modello non decide tutto in un colpo, ma fissa prima le celle di cui è più sicuro e poi ricalcola le altre tenendone conto.

- **Input aggiuntivo:** una "bozza" della griglia finale, con un embedding per ogni cella (un tile oppure il simbolo `[MASK]`), sommata ai token delle celle.
- **Inferenza:**
  1. un passaggio di M1 decide quali celle cambiano; quelle che non cambiano vengono fissate al tile riconosciuto;
  2. le celle che cambiano partono tutte come `[MASK]`;
  3. in 8 passi, a ogni passo si predicono le celle mascherate, si fissano le più sicure e si rimascherano le altre.
- **Addestramento:** sulla bozza si maschera una frazione casuale delle celle che cambiano (più qualche cella che non cambia, per robustezza); la loss si calcola solo sulle celle mascherate.
- **Bonus:** campionando invece di prendere il massimo si ottengono K uscite diverse, utili per la decodifica vincolata (sezione 8.6).

### 8.4 M2, l'editor a comandi

M2 usa gli stessi encoder e lo stesso corpo di M1, ma al posto delle teste ha un piccolo decoder (2 blocchi) che genera una sequenza di token:

- **Vocabolario:** `MOVE`, `ADD`, `REMOVE`, `REPLACE`, `END`, gli 11 tipi di tile, i numeri di riga (0–15) e di colonna (0–19).
- **Esempio:** `MOVE 1 4 3 4 END` sposta l'oggetto in (1, 4) nella cella (3, 4). Un ponte di tre celle diventa tre `ADD`; un `REPLACE` indica un rettangolo e i due tile.
- **Esecuzione:** un interprete Python applica i comandi alla griglia riconosciuta dalla testa di percezione.
- **Proprietà:** non tocca mai celle che i comandi non indicano. Se però sbaglia una coordinata, la modifica è sbagliata.

### 8.5 Le baseline nel dettaglio

- **B0, copia:** restituisce la griglia d'ingresso.
- **B1, regole:** riconosce le frasi da template con espressioni regolari e chiama l'esecutore. Legge la griglia dall'immagine con un confronto esatto con i tile noti (quindi fallisce anche sul tileset nuovo).
- **B2, LLM e VLM senza addestramento:** un prompt con la legenda dei simboli ASCII, il livello (in ASCII per [Qwen3](https://simonwillison.net/2025/Apr/29/qwen-3/) da 1,7B; come immagine per [Qwen3.5](https://www.producthunt.com/@binyuan_hui/activity) da 2B, nativamente multimodale), l'istruzione e la richiesta di restituire solo la griglia 16 × 20.
- **B3, InstructPix2Pix:** riceve immagine e istruzione e produce un'immagine; la riconvertiamo in griglia assegnando a ogni quadrato 14 × 14 il tile più simile.
- **B4, VLM con LoRA:** Qwen3.5 da 0,8B o 2B, encoder visivo congelato, LoRA di rango 16 sui blocchi del modello linguistico, addestrato a produrre la griglia ASCII.
- **Varianti di M1 per le ablation:** una U-Net della stessa taglia al posto del transformer (H4), un ViT da zero al posto di DINOv2 (H5), FiLM al posto della cross-attention ([FiLM](https://ojs.aaai.org/index.php/AAAI/article/view/11671)), M1 senza testa di modifica (H1).

### 8.6 Decodifica vincolata

Si applica a M1-iter, a M2 e a B4: si generano K = 8 uscite e si tiene la prima che rispetta le **regole di validità** (sezione 4.3).

Attenzione: si usano solo le regole di validità, non il verificatore dell'istruzione. Il verificatore conosce l'operazione corretta, quindi usarlo in inferenza sarebbe barare. Nel report si riportano sempre i risultati con e senza decodifica vincolata.

## 9. Addestramento

M1 si addestra in modo supervisionato sulle coppie del dataset, con quattro loss sommate. Tutti i numeri qui sotto sono punti di partenza da confermare con i primi run.

### 9.1 Le loss di M1

| Loss | Su quali celle | Formula | Note |
| --- | --- | --- | --- |
| Percezione | Tutte | Cross-entropy sulle 11 classi | Etichette gratis dal generatore |
| Modifica | Tutte | Binary cross-entropy con peso sulla classe "cambia" | Cambiano poche celle su 320: il peso compensa lo sbilanciamento. In ablation, focal loss |
| Nuovo tile | Solo quelle che cambiano | Cross-entropy sulle 11 classi |  |
| Raggiungibilità | Tutto il livello | Sezione 9.2 | Si attiva dopo le prime epoche |

```latex
L = L_{percezione} + L_{modifica} + L_{nuovo} + \lambda \, L_{raggiungibilita}
```

Il peso della classe "cambia" parte dal rapporto tra celle che non cambiano e celle che cambiano, calcolato sul train. λ vale 0 per il primo 20% dei passi, poi cresce linearmente fino a λ\_max, scelto in validazione tra 0,1 e 1.

### 9.2 La loss di raggiungibilità (il "flood fill morbido")

**L'idea in parole.** Si simula, in modo differenziabile, l'acqua che si espande dal giocatore attraverso le celle attraversabili. Se l'acqua non arriva alle scale, la loss è alta. Poiché tutto è fatto con probabilità e massimi, il gradiente torna fino alle teste del modello.

**I passi.**

1. Per ogni cella si calcola la distribuzione del tile finale: q = (1 − c) · percezione + c · nuovo tile, dove c è la probabilità di modifica.
2. p(cella) = somma delle probabilità dei tile attraversabili (pavimento, ponte, chiave, scale, giocatore).
3. r⁰ = probabilità che la cella contenga il giocatore.
4. Si ripete per T = 40 passi (più della distanza massima nella griglia):

```latex
r^{(t+1)}_v = p_v \cdot \max\Big( r^{(t)}_v,\; \max_{u \in N(v)} r^{(t)}_u \Big)
```

dove N(v) sono le 4 celle vicine di v.

5. La loss è il logaritmo negativo della probabilità di arrivare alle scale:

```latex
L_{raggiungibilita} = -\log\Big( \max_v \; r^{(T)}_v \, q_v(\text{scale}) + \varepsilon \Big)
```

**Con porte e chiavi, due fasi.** Fase A: il flood fill con le porte chiuse, che calcola anche la probabilità di raggiungere una chiave. Fase B: si riparte dalla zona raggiunta con le porte attraversabili, pesando il risultato per la probabilità di avere la chiave. La probabilità finale di arrivare alle scale è il massimo tra quella della fase A e quella della fase B.

**Implementazione.** Il massimo sui vicini è un max-pooling con un nucleo a croce, che in PyTorch si scrive spostando il tensore nelle 4 direzioni. Costa pochissimo.

**Precedente in letteratura.** Nella segmentazione medica esistono loss differenziabili che preservano la connettività, come soft-clDice, basata su una scheletrizzazione morbida ([clDice](https://arxiv.org/pdf/2003.07311v6)). La nostra applica lo stesso principio alla raggiungibilità in un livello di gioco.

### 9.3 Procedura e iperparametri di M1

| Aspetto | Valore di partenza |
| --- | --- |
| Ottimizzatore | AdamW, learning rate 3e-4, weight decay 0,05 |
| Parti pre-addestrate sbloccate (solo in ablation) | Learning rate 1e-5 |
| Schedule | Warmup lineare di 1.000 passi, poi coseno |
| Batch | 128 |
| Precisione | bf16 |
| Regolarizzazione | Dropout 0,1, gradient clipping a 1,0 |
| Durata | 30–50 epoche, early stopping sul "successo pieno" in validazione |
| Curriculum | Prime 5 epoche solo operazioni singole, poi il mix di 1–2 operazioni |
| Ripetizioni | 3 seed per i risultati principali |

**Augmentation.**

- Tileset scelto a caso tra quelli di train, e variazioni di colore e luminosità.
- Specchiature orizzontali e verticali, applicate in modo coerente a griglie, maschera e programma. L'istruzione si rigenera dal template con la relazione scambiata (*left* ↔ *right*, *top-left room* ↔ *top-right room*). Non si applica alle istruzioni riformulate o umane.

**Efficienza.** I due encoder sono congelati: gli embedding del testo si possono calcolare una volta sola e salvare. DINOv2-S è abbastanza leggero da girare a ogni batch, il che permette le augmentation sulle immagini.

### 9.4 Gli altri modelli

| Modello | Come si addestra |
| --- | --- |
| M1-iter | Si parte dai pesi di M1 e si continua con la bozza mascherata (sezione 8.3) per 10–20 epoche |
| M2 | Cross-entropy sui token del programma con *teacher forcing*, label smoothing 0,1; in inferenza beam search con 4 candidati |
| B4 | LoRA di rango 16 (alpha 32), learning rate 1e-4, encoder visivo congelato, 1–2 epoche su un sottoinsieme di 50.000 esempi |
| Varianti di ablation | Come M1, cambiando un solo componente |

### 9.5 Stima del calcolo

- **M1:** circa 15M parametri addestrabili e 320 token per esempio: nell'ordine di poche ore per run su una GPU moderna da 16–24 GB.
- **Esperimenti totali:** M1, M1-iter e M2 con 3 seed, più circa 6 ablation con 1–3 seed: in tutto circa 30 run.
- **B4:** da qualche ora a circa una giornata di GPU, a seconda della taglia (0,8B o 2B).
- **Valutazione:** automatica, minuti per split.

Il primo run completo serve anche a misurare questi tempi e ad aggiornare il piano.

## 10. Valutazione

Tutta la valutazione è automatica e si fa sulla griglia finale, mai sull'immagine. La metrica principale è il **successo pieno**: istruzione eseguita, nessuna modifica non richiesta, livello valido.

### 10.1 Le metriche

| Metrica | Definizione | Cosa dice |
| --- | --- | --- |
| **Successo** | Il verificatore dell'istruzione risponde "sì" | Ha fatto ciò che era chiesto? |
| **Modifiche non richieste** | Numero di celle cambiate fuori dalla maschera; si riportano la media e la % di esempi con zero | Ha rovinato il resto? |
| **Validità** | Tutte le regole della sezione 4.3, raggiungibilità compresa | Il livello è ancora giocabile? |
| **Successo pieno** | Successo + zero modifiche non richieste + validità | **La metrica principale** |
| Corrispondenza esatta | Griglia identica al ground truth (solo versione canonica) | Utile come controllo, troppo severa con risposte multiple |
| Accuratezza di percezione | % di celle riconosciute correttamente dall'immagine iniziale | Separa gli errori di "vista" da quelli di "ragionamento" |

### 10.2 Come riportiamo i risultati

- Ogni metrica su ogni split della sezione 6.5.
- Per i modelli addestrati: media e deviazione standard su 3 seed.
- Intervalli di confidenza al 95% con bootstrap sugli esempi di test.
- Parametri e tempo di inferenza di ogni modello, per il confronto M1 contro B4.

### 10.3 Analisi degli errori

Su un campione di errori classifichiamo ogni fallimento in una categoria:

1. **Percezione:** tile riconosciuto male nell'immagine iniziale.
2. **Oggetto sbagliato:** ha spostato o tolto l'oggetto sbagliato.
3. **Posizione sbagliata:** oggetto giusto, relazione spaziale sbagliata.
4. **Danni collaterali:** celle cambiate fuori dalla maschera.
5. **Livello rotto:** istruzione eseguita ma uscita non più raggiungibile.
6. **Incoerenza:** soluzione "a metà" tra più risposte possibili (es. ponte spezzato).

### 10.4 Le ablation

| Ablation | Ipotesi | Cosa si confronta |
| --- | --- | --- |
| Senza testa di modifica | H1 | Una sola testa "tile finale" contro le tre teste |
| λ = 0 | H2 | Senza contro con loss di raggiungibilità |
| M1 contro M1-iter | H3 | Sul dataset ambiguo |
| U-Net al posto del transformer | H4 | Visione locale contro globale |
| ViT da zero al posto di DINOv2 | H5 | Pre-addestramento, sul tileset nuovo |
| FiLM al posto della cross-attention | — | Due modi di unire testo e immagine |
| Con e senza decodifica vincolata | — | Quanto aiuta campionare K uscite |

### 10.5 Le figure del report

1. **Figura 1:** un esempio completo (immagine, istruzione, uscita, maschera).
2. **Figura 2:** l'architettura di M1.
3. **Tabella 1:** risultati principali, modelli per split, con il successo pieno.
4. **Figura 3:** il successo pieno per split, per i modelli principali, per vedere dove cala la generalizzazione.
5. **Figura 4:** esempi qualitativi di successi ed errori, anche su livelli reali (con la nostra grafica).
6. **Tabella 2:** le ablation.

## 11. Piano di lavoro

Dieci settimane, sei fasi in ordine. Ogni fase produce qualcosa che serve alla successiva. In tre punti c'è un **controllo** (gate): se non passa, si applica il piano B della sezione 13 prima di andare avanti.

&#91;embedded content: piano di lavoro · 6 fasi in 10 settimane, con 3 controlli\]

### 11.1 Le fasi in dettaglio

| Fase | Settimane | Cosa si fa | Si chiude quando |
| --- | --- | --- | --- |
| F1 · Mondo e generatore | 1–2 | Tile, regole di validità, BFS con chiavi e porte, relazioni spaziali, generatore delle 3 forme, test unitari | **G1:** i livelli generati sono tutti validi e i test passano |
| F2 · Dataset v1 | 3 | Operazioni (precondizione, esecutore, verificatore, maschera), template e riformulazioni, rendering, split; baseline B0 e B1 | Dataset v1 su disco, B0 e B1 valutati |
| F3 · M1 base | 4–5 | M1 con le 3 teste, senza loss di raggiungibilità; B2 e B3 zero-shot | **G2:** M1 batte B0 sul successo pieno, nello split IID |
| F4 · Estensioni | 6–7 | Loss di raggiungibilità, M1-iter, M2, B4 con LoRA, decodifica vincolata | Tutti i modelli addestrati su 3 seed |
| F5 · Livelli reali e ablation | 8 | Zelda NES dal VGLC, Link's Awakening con PyBoy, le 300 istruzioni umane, le ablation della sezione 10.4 | **G3:** tutti i numeri del report sono pronti |
| F6 · Report e demo | 9–10 | Figure, scrittura del report, demo Gradio, pulizia del repository | Consegna |

### 11.2 Tre filoni in parallelo

Dalla settimana 3 il lavoro si divide in tre filoni indipendenti:

1. **Mondo e dati:** generatore, operazioni, istruzioni, rendering; poi la raccolta delle istruzioni umane.
2. **Modelli:** M1, M1-iter, M2, le baseline, l'addestramento.
3. **Valutazione e livelli reali:** metriche e script delle tabelle; estrazione dallo Zelda NES e da Link's Awakening.

**Cosa anticipare.** Un prototipo dell'estrazione con PyBoy conviene farlo già nelle settimane 1–2: è la parte più incerta e non dipende da nient'altro. Se si blocca, si passa subito al piano B (solo dungeon, o solo VGLC).

## 12. Struttura del codice

Un solo repository Python, organizzato per moduli indipendenti, con configurazioni YAML e test unitari sulle parti che decidono la correttezza (regole, operazioni, verificatori).

```
leveledit/
  world/        tile, regole di validità, BFS con chiavi e porte, relazioni spaziali
  generator/    generazione dei livelli (3 forme), filtro di validità
  ops/          MOVE, ADD, REMOVE, REPLACE: precondizione, esecutore, verificatore, maschera
  language/     template, riformulazioni con LLM, test umano
  render/       tileset CC0, rendering a 14 px per cella, augmentation
  data/         costruzione del dataset e degli split, caricamento in PyTorch
  real/         parser VGLC (Zelda NES), estrazione con PyBoy (Link's Awakening), tabelle di conversione
  models/       M1, M1-iter, M2, varianti di ablation, flood fill morbido
  baselines/    B0, B1, prompt per B2, B3, addestramento LoRA di B4
  train/        loop di addestramento, configurazioni, checkpoint
  eval/         metriche, analisi degli errori, tabelle e figure del report
  demo/         interfaccia Gradio: livello + istruzione -> risultato
configs/        un file YAML per ogni esperimento
tests/          test unitari (pytest)
notebooks/      esplorazione e figure
```

**Regole di lavoro:**

- Ogni esperimento si lancia da un file di configurazione, con seed fissati per `random`, `numpy` e `torch`.
- Le ipotesi della sezione 3 si salvano nel repository, con la data, prima dei run.
- I numeri del report si generano da script in `eval/`, mai copiati a mano.
- La ROM e i dati estratti restano fuori dal repository (in `.gitignore`).

## 13. Rischi e piano B

Nessun rischio blocca il progetto: per ognuno c'è una via d'uscita che produce comunque un risultato da riportare.

| Rischio | Segnale che sta succedendo | Piano B |
| --- | --- | --- |
| Il compito è troppo facile | M1 supera il 95% di successo pieno su tutti gli split | Aumentare la difficoltà: composizioni più lunghe, istruzioni umane, livelli reali, più riferimenti relativi |
| M1 non generalizza alle composizioni | Forte calo sullo split composizionale | Il confronto con M2 e l'analisi degli errori diventano il risultato principale |
| Il flood fill morbido è instabile | Loss che esplode o validità che peggiora con λ > 0 | Si tiene λ piccolo o nullo e si usa la decodifica vincolata, che non richiede addestramento |
| M1-iter non batte M1 | Nessuna differenza sul dataset ambiguo | Risultato negativo da spiegare; la versione canonica del dataset resta valida |
| L'estrazione da Link's Awakening richiede troppo tempo | Dopo una settimana non si leggono ancora stanze affidabili | Ci si limita alle stanze dei dungeon, o anche solo allo Zelda NES dal VGLC |
| B4 è troppo costoso | Un'epoca richiede più di un giorno | Si usa Qwen3.5 da 0,8B, o un sottoinsieme più piccolo del train |
| Le riformulazioni dell'LLM cambiano il significato | Molti errori nel controllo manuale del campione | Si riducono le riformulazioni e si dà più peso al test umano |

## 14. Posizionamento rispetto ai lavori esistenti

Non abbiamo trovato un modello *addestrato* che modifica livelli di gioco da un'istruzione, con un benchmark su conservazione, validità e composizione. Prima di consegnare va fatta una ricerca bibliografica più accurata.

| Lavoro | Cosa fa | Differenza con LevelEdit |
| --- | --- | --- |
| [MarioGPT](https://www.academia.edu/110737482/MarioGPT_Open_Ended_Text2Level_Generation_through_Large_Language_Models) | Genera livelli di Mario da un prompt testuale | Genera da zero, non modifica un livello esistente |
| [Agentic PCG](https://zehua-jiang.github.io/AgenticPCG) | Un agente LLM modifica livelli in più passi con dei tool | Sistema basato su tool, non un modello addestrato; nessun benchmark di conservazione |
| Riparazione di livelli ([es.](https://export.arxiv.org/pdf/2506.19359)) | Rende funzionante un livello rotto, a volte con il vincolo di poche modifiche | Non segue istruzioni |
| [Progetto del corso sulle NCA (Zelda)](https://github.com/NicoPozio/zelda-nca) | Ripara stanze danneggiate dello Zelda NES; trova che la località è il collo di bottiglia | Nessuna istruzione; noi usiamo un modello globale e un vincolo esplicito di raggiungibilità |
| [gSCAN](https://par.nsf.gov//servlets/purl/10217557) | Benchmark di istruzioni in un mondo a griglia, con split di generalizzazione composizionale | Le istruzioni si eseguono come azioni di un agente, non come modifiche del mondo; ne riprendiamo il disegno degli split |
| InstructPix2Pix | Modifica foto da istruzioni | Output in pixel e valutazione soggettiva; noi usiamo un output discreto e verificabile |
| [MaskGIT](https://arxiv.org/pdf/2202.04200) | Generazione di immagini con decodifica iterativa in parallelo | Ne prendiamo il metodo per M1-iter |

**Aree del corso coperte**, tutte tra quelle che non richiedono approvazione preventiva: gaming and AI, multimodal learning, image/video generation, program synthesis, reasoning. Nessun dominio escluso dalle linee guida.

## 15. Il report finale

Per un gruppo da 3 il corpo del report è di 4 pagine, nel template del corso; riferimenti, appendice e dichiarazione sull'uso dell'AI non contano nel limite ([linee guida](https://github.com/erodola/DLAI-s2-2026)).

### 15.1 Regole del corso da rispettare

- **Template ufficiale** DLAI, a due colonne.
- **Statement on the use of AI**, obbligatorio.
- **Dimensione adeguata al gruppo:** un gruppo più grande deve consegnare un progetto più grande, e questo è un criterio di valutazione.
- **Consegna:** link al repository e report, via email al docente e ai suoi collaboratori, come indicato nelle linee guida.

### 15.2 Struttura proposta delle 4 pagine

| Sezione | Spazio indicativo | Contenuto |
| --- | --- | --- |
| Introduzione | 0,5 pagine | Il problema, la Figura 1, i tre contributi |
| Lavori correlati | 0,3 pagine | La tabella della sezione 14, in forma di testo |
| Mondo e dataset | 0,8 pagine | Regole, operazioni, verificatori, split |
| Metodo | 0,9 pagine | M1 (Figura 2), M1-iter, loss di raggiungibilità, M2 |
| Esperimenti | 1,2 pagine | Tabella 1, Figura 3, ablation, livelli reali |
| Limiti e conclusioni | 0,3 pagine | Cosa non funziona, cosa resta aperto |
| Appendice (fuori limite) | Libero | Iperparametri, dettagli del generatore, altri esempi, analisi degli errori |

### 15.3 Consigli di forma

Presi da cosa distingueva i progetti migliori del corso che abbiamo analizzato.

- **Titolo che enuncia il risultato** principale, non solo l'argomento. Si sceglie alla fine, quando i numeri ci sono.
- **Ipotesi dichiarate prima** e richiamate nei risultati, anche quando sono smentite.
- **Limiti espliciti:** cosa il modello non sa fare e perché.
- **Repository riproducibile:** README con i comandi per rigenerare dataset, addestrare e valutare; checkpoint dei modelli; demo Gradio.

## 16. Riferimenti

**Modelli e metodi**

- [DINOv2, model card (patch 14, ViT-S/B/L/g)](https://huggingface.co/spaces/multimodalart/InstantID-FaceID-6M/blob/2bf7ead51a0a9f924abc62b7bb20b154e28ae436/torchhub/facebookresearch_dinov2_main/MODEL_CARD.md)
- [MaskGIT: Masked Generative Image Transformer](https://arxiv.org/pdf/2202.04200)
- [FiLM: Visual Reasoning with a General Conditioning Layer](https://ojs.aaai.org/index.php/AAAI/article/view/11671)
- [clDice: a Topology-Preserving Loss Function](https://arxiv.org/pdf/2003.07311v6)
- [Qwen 3](https://simonwillison.net/2025/Apr/29/qwen-3/) e [Qwen3.5 Small](https://artificialanalysis.ai/articles/qwen3-5-small-models)

**Benchmark e lavori correlati**

- [gSCAN: A Benchmark for Systematic Generalization in Grounded Language Understanding](https://par.nsf.gov//servlets/purl/10217557)
- [MarioGPT: Open-Ended Text2Level Generation through Large Language Models](https://www.academia.edu/110737482/MarioGPT_Open_Ended_Text2Level_Generation_through_Large_Language_Models)
- [Agentic PCG](https://zehua-jiang.github.io/AgenticPCG)
- [Evolutionary level repair](https://export.arxiv.org/pdf/2506.19359)
- [Complessità dei puzzle di Zelda (chiavi e porte)](https://arxiv.org/pdf/2203.17167)

**Dati e strumenti**

- [The Video Game Level Corpus (VGLC)](https://www.github.com/TheVGLC/TheVGLC) e [articolo](https://arxiv.org/pdf/1606.07487v1)
- [PyBoy, emulatore Game Boy in Python](https://docs.pyboy.dk/)
- [RAM map di Link's Awakening](<https://datacrystal.tcrf.net/wiki/The_Legend_of_Zelda:_Link%27s_Awakening_(Game_Boy)/RAM_map>)
- [Mappe interne di Link's Awakening](https://zeldaspeedruns.com/la/doghouse/in-game-maps)
- [LADXR, randomizer in Python](https://git.hollymcfarland.com/monorail/Archipelago/src/commit/43874b1d28fa8d5a5bdc96d4408e303f57763ddd/worlds/ladx/LADXR)
- [MiniGrid](https://minigrid.farama.org/)

**Progetti del corso citati**

- [Zelda NCA: riparazione di stanze](https://github.com/NicoPozio/zelda-nca)
- [Mean or Mode: colorizzazione](https://github.com/solazzo1911897-collab/colorization-mean-vs-mode)
- [Repository ufficiale del corso DLAI 2026](https://github.com/erodola/DLAI-s2-2026)
