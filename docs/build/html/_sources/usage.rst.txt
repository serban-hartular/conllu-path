Usage
=====

.. _installation:

Installation
------------

To use conllu-path, first install it using pip:

.. code-block:: console

   (.venv) $ pip install lark
   (.venv) $ pip install -i https://test.pypi.org/simple/ conllu-path-shartular

Sample usage
--------------------

Import the package, and load your conllu file into a doc. The examples below use
part of the reference Romanian-language UD corpus, RoRefTrees.

    >>> import conllu_path as cp
    >>> doc = cp.Doc.from_conllu('../ro_rrt-ud-train.conllu')

(The following examples assume you know something about the conllu annotation format. If
you don't, consult https://universaldependencies.org/, the homepage of the corpus
you are using and, of course, browse the corpus yourself.)

Now I'm going to search the doc for the plural form of the noun *vis*
(meaning *dream*). I'm doing this because I know this noun has two possible plurals,
*vise* and *visuri*, and I would like to see what context each is used in. To do this,
I am going to use the ``Doc.search`` function, which searches through all the
sentences in a doc, starting at the root of each sentence. Its argument is the
following search expression:

``'.//[lemma=vis upos=NOUN feats.Number=Plur]'``.

The search expression consists of a path prefix (``.//``), and a set of conditions
that a node must fulfill in order to match the search expression, in
square brackets. The path prefix indicates what nodes are included in the search:
``.//`` means "the current node and all its descendants" -- which, in doc and sentence
searches, means all nodes. The conditions inside the square brackets mean that
a node will match only if its *lemma* is *vis*, if its *upos* (universal part-of-speech)
is *NOUN*, and if, among its morphological features (*feats*), the *Number*
feature is *Plur*, singifying plural.

    >>> for match in doc.search('.//[lemma=vis upos=NOUN feats.Number=Plur]'):
    ...     print(match, ' -- ', match.sentence())
    5:vise  --  Era unul din acele vise care, deși păstrează decorul caracteristic viselor, sunt o continuare a activității intelectului și în care devii conștient de anumite fapte și idei care ți se par inedite și valoroase și după ce te trezești. (sent_id=train-590)
    12:viselor  --  Era unul din acele vise care, deși păstrează decorul caracteristic viselor, sunt o continuare a activității intelectului și în care devii conștient de anumite fapte și idei care ți se par inedite și valoroase și după ce te trezești. (sent_id=train-590)
    15:vise  --  Peisajul pe care-l avea în fața ochilor îi revenea atât de frecvent în vise, încât niciodată nu era pe deplin sigur dacă îl văzuse sau nu în realitate. (sent_id=train-599)
    8:visurile  --  un vizionar al cărui destin, cu visurile și faptele sale de vitejie, a rămas pentru totdeauna în istorie, contribuind la modelarea lumii, așa cum o cunoaștem astăzi. (sent_id=train-1362)
    17:vise  --  / / Plâns de ape se repetă / Încă totu-i adormit – / Ca în vise s-a pornit / Roata morii – violetă. (sent_id=train-2687)
    29:vise  --  / / Cioplindu-și-o cu mâinile subțiri, / neîntrecutul meșter din Cremona, / încă-nainte de-a o isprăvi, / i-a ascultat în vise melodia. (sent_id=train-2833)
    4:vise  --  Crea din nou vise, căutând să mă formeze pentru ele. (sent_id=train-2995)
    11:vise  --  Nu știți că vă așteaptă deșteptarea, Nebuni hrăniți cu vise? (sent_id=train-3162)
    6:vise  --  În sufletu-mi buchetele de vise Au înflorit când înflorea răsura. (sent_id=train-3376)
    1:Visele  --  Visele sunt semne de dragoste. (sent_id=train-3538)
    11:visurile  --  Realltatea e un monstru hidos, hrănit cu iluziile și visurile noastre. (sent_id=train-3564)

The search returns 11 results, of which only the second and the last have plurals with the
*-uri* desinence, as opposed to the *-e* desinence. A good Romanian language dictionary
will tell you that the *-uri* ending is used when the word *vis* means dream=aspiration,
and the *-e* ending for the literal sense of dream=vision-while-sleeping. These examples
confirm what the dictionary says.

The ``doc.search`` function returns a generator of ``Tree`` objects. ``Tree`` objects
represent nodes in the sentence dependency tree, one node for each token (word,
punctuation, etc.) in the sentence. I can inspect the content of the annotation
for a node using the ``Tree.data`` function:

>>> match.data('form')
'visurile'
>>> match.data('feats.Gender')
{'Fem'}

Morphological features and annotations in the ``misc`` section are stored as sets,
since a feature can have more than one value. Repeatedly getting the value of the sole member
of a set can be a pain, so you can get the content of any annotation in string form
using the ``Tree.sdata`` function.

>>> match.sdata('feats.Gender')
'Fem'

(If the feature has multiple values, they will be joined by commas and returned
as a string.)

Using ``Tree.data`` without an argument will return the entire annotation of the node
in dictionary form:

>>> match.data()
{'id': '11', 'form': 'visurile', 'lemma': 'vis', 'upos': 'NOUN', 'xpos': 'Ncfpry', 'feats': {'Case': {'Nom', 'Acc'}, 'Definite': {'Def'}, 'Gender': {'Fem'}, 'Number': {'Plur'}}, 'head': '9', 'deprel': 'conj', 'deps': None, 'misc': None}

It's possible to search for multiple feature values at once, e.g. ``lemma=vis,coșmar`` will
match nodes whose lemma is either *vis* or *coșmar* (nightmare). Feature values
can also be matched against regular expressions enclosed in curly braces. For
instance, ``lemma={filo.*}`` will match any lemma that starts with 'filo'.

Search requirements can be combined using the logical operators *and* (``&``),
*or* (``|``) and *not* (``!``), and grouped using parentheses. The order of
operations is *not*, *and*, *or*.
Space-separated requirements (as in the example
above) are implicitly and-ed. If I want to search for a verb that is used as an
auxiliary or has the lemma *putea*, my search string would be

    ``.//[upos=VERB (deprel=aux | lemma=putea) ]``

If your corpus is very large, loading all of it to the memory can pose problems. Corpora
can be iterated through (by sentence), using the
``conllu_path.iter_sentences_from_conllu`` function:

    >>> for sentence in cp.iter_sentences_from_conllu('../ro_rrt-ud-train.conllu'):
    ...     for match in sentence.search('.//[lemma=vis upos=NOUN feats.Number=Plur]'):
    ...         print(match.data('form'), '\t', match.uid(), '\t', match.sentence())
    vise     train-590/5     Era unul din acele vise care, deși păstrează decorul caracteristic viselor, sunt o continuare a activității intelectului și în care devii conștient de anumite fapte și idei care ți se par inedite și valoroase și după ce te trezești. (sent_id=train-590)
    viselor          train-590/12    Era unul din acele vise care, deși păstrează decorul caracteristic viselor, sunt o continuare a activității intelectului și în care devii conștient de anumite fapte și idei care ți se par inedite și valoroase și după ce te trezești. (sent_id=train-590)
    vise     train-599/15    Peisajul pe care-l avea în fața ochilor îi revenea atât de frecvent în vise, încât niciodată nu era pe deplin sigur dacă îl văzuse sau nu în realitate. (sent_id=train-599)
    visurile         train-1362/8    un vizionar al cărui destin, cu visurile și faptele sale de vitejie, a rămas pentru totdeauna în istorie, contribuind la modelarea lumii, așa cum o cunoaștem astăzi. (sent_id=train-1362)
    vise     train-2687/17   / / Plâns de ape se repetă / Încă totu-i adormit – / Ca în vise s-a pornit / Roata morii – violetă. (sent_id=train-2687)
    vise     train-2833/29   / / Cioplindu-și-o cu mâinile subțiri, / neîntrecutul meșter din Cremona, / încă-nainte de-a o isprăvi, / i-a ascultat în vise melodia. (sent_id=train-2833)
    vise     train-2995/4    Crea din nou vise, căutând să mă formeze pentru ele. (sent_id=train-2995)
    vise     train-3162/11   Nu știți că vă așteaptă deșteptarea, Nebuni hrăniți cu vise? (sent_id=train-3162)
    vise     train-3376/6    În sufletu-mi buchetele de vise Au înflorit când înflorea răsura. (sent_id=train-3376)
    Visele   train-3538/1    Visele sunt semne de dragoste. (sent_id=train-3538)
    visurile         train-3564/11   Realltatea e un monstru hidos, hrănit cu iluziile și visurile noastre. (sent_id=train-3564)

In this example, I displayed each node's unique ID, (``Tree.uid()``), which consists
of the sentence id, a backslash, and the ID of the node within the sentence. You can
get a node from a doc by its UID:

>>> doc.get_node('train-3538/1'), doc.get_node('train-3538/1').sentence()
(1:Visele, Visele sunt semne de dragoste. (sent_id=train-3538))


A search can include requirements for a node's children, descendants, or
parent. In the next search, I am looking for the verbal pro-form *a o face* (to
do it/this), consisting of the verb *face* and the feminine pronominal clitic *o*
in the role of the direct object. The search string is

    ``'.//[lemma=face /[deprel=obj form=o,-o,o-] ]'``

The nodes I am looking for must have the ``lemma`` *face*. The next requirement,
``/[deprel=obj form=o,-o,o-]``, means the node must have a child (the ``/`` prefix)
whose ``deprel`` is ``obj`` (direct object) and whose ``form`` is *o*, *-o*, or *o-*
(because a clitic can be connected to an adjacent word with a dash.)

    >>> for match in doc.search('.//[lemma=face /[deprel=obj form=o,-o,o-] ]'):
    ...     print(match.sentence())
    este creat de o celulă care a primit o genă (ADN) care o face capabilă să producă factorul uman VIII de coagulare. (sent_id=train-4152)
    Când o vor face, viața lor la curte va deveni mult mai ușoară. (sent_id=train-4777)
    Răpirea a fost aparent săvârșită de o celulă de teroriști internaționali, și asta o face automat o problemă de securitate de stat. (sent_id=train-4924)
    Consfătuirea poate dezvălui dezordinea și o poate aduce la suprafață, dar dacă o face, acea harababură va fi existat cu mult înaintea procesului de consfătuire. (sent_id=train-5073)
    Am făcut-o cu atâta forță, totuși, că m-am tăiat puțin la buza de jos la marginea instrumentului negru, dur. (sent_id=train-5320)
    și deși pielea se întărește la soare pentru a se proteja, nu o face și într-un solar. (sent_id=train-5374)
    Obiectivul general stabilit în art. 1 este de a întări acțiunea comunitară în domeniul culturii și de a o face mai eficientă prin acordarea de asistență organismelor care activează în acest domeniu. (sent_id=train-5983)
    Clinchetul paharelor ciocnite, izul de vin risipit pe mesele de fag, toate o făceau să fie veselă fără să știe de ce. (sent_id=train-6791)

Searching the structure of the dependency tree is better than a sequential search in
this case because the position of the clitic can vary depending on the mood and tense
of the verb: it can precede the verb (*nu o face*), follow it (*Am făcut-o*), be
separated from the verb by an auxiliary (*o vor face*).

Now suppose I want to find some ellipses. Specifically, I am looking for situations
where the verb *a vrea* (to want), a transitive verb, is used without its direct
object. My search string is

    ``'.//[lemma=vrea upos=VERB !/[deprel=obj,ccomp,xcomp] ]'``

The node's lemma must be *vrea* and its part of speech must be ``VERB``, to exclude
the uses of *vrea* as an auxiliary. The next requirement, ``!/[deprel=obj,ccomp,xcomp]``,
is that the node must *not* (the ``!`` operator) have a child (the ``/`` path prefix)
whose ``deprel`` is ``obj`` (nominal direct object), ``ccomp`` (clausal direct object)
or ``xcomp`` (secondary object).

    >>> for match in doc.search('.//[lemma=vrea upos=VERB !/[deprel=obj,ccomp,xcomp] ]'):
    ...     print(match.sentence())
    Nu vroia dar în final devenise conștientă de ora târzie printr-un căscat; se întâmplă deja înainte ca ea să-l poată opri. (sent_id=train-5394)
    (" Nu vreau gratis, domnule, se justifica Hagienuș peste tot, nu vreau să fiu întreținut de copii. (sent_id=train-6690)

The search returns two sentences where the verb *vrea* is used without a direct object:
*Nu vroia dar în final devenise conștientă...*, i.e. *She didn't want to, but finally she became aware...*,
and *Nu vreau gratis*, i.e. *I don't want [to receive anything] for free*.

Sometimes it is desirable for the search to capture both the matching node and
the descendant(s) of that node that was part of the search. Suppose I want to see
what adjectives are used in a text to describe the noun *fată* (girl). My search
string will be:

    ``'.//[upos=NOUN lemma=fată]/[deprel=amod upos=ADJ]'``

Here, the part of the search expression that describes the subordinate adjective,
``/[deprel=amod upos=ADJ]``, is outside the square brackets of the expression
describing the noun. It follows the first expression, as if describing a path
to the node.

    >>> for match in doc.search('.//[upos=NOUN lemma=fată]/[deprel=amod upos=ADJ]'):
    ...     print(match, match.next_matches, match.sentence())
    Match(18:fată) [Match(19:singură)] Odată recunoscut, nu mai putea merge să se așeze la o masă unde stătea deja o fată singură. (sent_id=train-271)
    Match(5:fată) [Match(6:bolnavă)] Orașul este „o fată bolnavă în agonie ”, casele par „femei tăcute ”, poetul se închipuie într-un sanatoriu, unde moartea face parte din cotidian. (sent_id=train-2839)
    Match(58:fată) [Match(59:mare)] Tu, bubă veninată, bubă din bere, din mâncare, din bătaia vântului, din boarea pământului, să ieși de la cutare din cap, din inimă, din trupul lui, din toate inchieturile să ieși și să te duci în vânturile mari, peste munți, unde popă nu toacă, unde fată mare coadă nu împletește, unde câne nu latră. (sent_id=train-3516)
    Match(11:fete) [Match(10:grațioase)] Unul dintre cele mai pregnante studii este al unei grațioase fete de zece ani care s-a înecat câțiva ani mai târziu într-un accident de canotaj pe Mississippi. (sent_id=train-5188)
    Match(21:fetele) [Match(22:nemăritate)] Ăl mai mare era Oprică al lui coana Mărita, una de da în cărți și făcea de dragoste la fetele nemăritate. (sent_id=train-6810)

The adjectives that describe the noun *fată* are *singură* (alone), *bolnavă* (sick),
*mare* (big/old, i.e. an old maid), *grațioasă* (graceful), *nemăritată* (unmarried).

When the search expression consists of a path (rather than the description of a
single node), ``doc.search`` returns a ``Match`` object instead of a ``Tree`` object
A ``Match`` object has a ``node`` attribute that points to the node itself,
and a ``next_nodes`` attribute, a list of the nodes that matched the next element
in the path. The next element in the path can match multiple nodes. In the
next example, I extract those situations where multiple adjectives
are used together to describe the noun *familie*, family:

    >>> for match in doc.search('.//[upos=NOUN lemma=familie]/[deprel=amod upos=ADJ]'):
    ...     if len(match.next_matches) > 1:
    ...         print(match, match.next_matches, match.sentence())
    Match(16:familie) [Match(15:singură), Match(17:imensă)] În vagonul în care călătorise el, băncile de lemn erau supraaglomerate de o singură familie imensă, de la o străbunică știrbă până la un copil de o lună: se duceau cu toții la țară, la niște neamuri, să petreacă o după-amiază și, așa cum îi explicaseră lui Winston, deși el nu-i întrebase, ca să facă rost de niște unt pe sub mână. (sent_id=train-422)
    Match(10:familie) [Match(9:veche), Match(11:boierească)] Prin tată, B. se trăgea dintr-o veche familie boierească (Mustea), atestată pe vremea lui Ștefan cel Mare. (sent_id=train-2680)
    Match(6:familii) [Match(7:irlandeze), Match(9:nebune)] Descrierea lui Ronan a unei familii irlandeze puțin nebune este numai suficient de răutăcioasă ca să rămână pe partea mai dură a sentimentalului, povestirea sa despre dispariția înceată a unei prietenii inconfortabil de convingătoare. (sent_id=train-5091)

Families are described in the corpus as being *singură, imensă* (alone, huge),
*veche, boierească* (old, aristocratic), *irlandeză, nebună* (Irish, crazy).

(Note that this search won't capture adjectives that are connected by coordination
since, in the UD annotation, the second item in a coordinated construction is
connected to the first item, not to their grammatical regent. A search for coordinated
adjectives would have to look like this:

    ``'.//[upos=NOUN lemma=lemma]/[deprel=amod upos=ADJ]/[deprel=conj upos=ADJ]'``

where deprel=conj means 'is connected to the previous item by a relationship of coordination.
Searches have to take into account the way the UD dependency trees are structured.)

So far, I've shown examples of searches applying to entire docs or sentences.
Searches can start from individual nodes as well, using a ``Search`` object.
The ``Search`` object is built by passing a search expression to the constructor.
It implements a ``Search.match`` function that takes a node as its argument and
returns a list of nodes that match the search, starting at that node. For example,
let's pick a node in the doc:

    >>> node = doc.get_node('train-3303/14')
    >>> node
    14:depărteze

This node has a number of children.

    >>> node.children()
    [4:că, 5:prețul, 11:să, 12:nu, 13:se, 15:mult, 16:,, 17:în, 31:arenda]

I can search, starting at this node, for those children that are: nouns,
subordinating conjunctions, adverbs, or particles:

    >>> cp.Search('/[upos=NOUN]').match(node)
    [5:prețul, 31:arenda]
    >>> cp.Search('/[upos=SCONJ]').match(node)
    [4:că]
    >>> cp.Search('/[upos=ADV]').match(node)
    [15:mult]
    >>> cp.Search('/[upos=PART]').match(node)
    [11:să, 12:nu]

Since the ``Search.match`` function returns an empty list if no matching node
is found, it can be used in list comprehensions -- in the next example, to build
a list of those nodes that are either subordinate conjunctions or particles:

>>> [n for n in node.children() if cp.Search('.[upos=SCONJ,PART]').match(n)]
[4:că, 11:să, 12:nu]

Note that in this case, the path prefix is ``.``, meaning that the search is
happenning on the current node (not on its children or descendants).