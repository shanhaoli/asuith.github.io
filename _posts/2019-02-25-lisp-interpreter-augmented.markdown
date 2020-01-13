---
layout: article
title: '如何用 Python 写一个 Lisp 的解释器'
date: '2019-02-25 15:48:30 +0800'
categories: cs
---
如何写一个 Lisp 的解释器 (*Interpreter*)？这个问题很好解决，只要找一个好的教程，发挥自己的聪明才智，一步一步地坚持做，最终就能完成。

最近我看了 Peter Norvig 写成的 [(How to Write a (Lisp) Interpreter (in Python))](http://www.norvig.com/lispy.html) ，然后仿造着也写了一个，并且在原有的基础上添加了关键词 `cond` 与 `let` 的功能。 

# 原文章介绍

先简单介（翻）绍（译）一下原文章。

> *If you don't know how compilers work, then you don't know how computers work.* -[Steve Yegge](http://steve-yegge.blogspot.com/2007/06/rich-programmer-food.html)

我并不认识这位 Steve Yegge，也不知道他说的话有多大分量，不过既然 Norvig 的原文章把这话放在开头，大概能唬到人吧。

原文是用 Python 3 实现了 Scheme（Lisp 的的方言）的大部分功能，代码清晰简洁。作者将其取名为 Lispy （[**lis.py**](https://github.com/norvig/pytudes/blob/master/py/lis.py)）。

Scheme 语言本身就异常简洁：

- Scheme 程序只由 `expression` 构成。
- `number` (e.g. 42)和 `symbol` (e.g. r)是 Scheme 语句中最小的成分。这点与其他语言类似，不过在Scheme中，+ 和 > 这种也被当做 `symbol` 来处理。
- 除了 `number` 和 `symbol` ，其他所有的东西都是一个 `list expression`，形式是左右括号中夹着一个或多个 `expression` 。括号中的第一个 `expression` 决定了这个语句的意义：
  - 如果是关键词（keyword），那取决于关键词的含义。e.g. (+ 1 2) 就是把 1 与 2 相加。
  - 如果不是关键词，那就是一个函数。e.g. (sqrt x) 就是取 x 的平方根 (sqrt 即为 square root)。

如果有编译原理训练或者对 Lisp 有所了解的同学可以看出，这语言其实是递归定义出来的，程序到最后肯定会有很多右括号。曾经有个笑话就是说，某敌方间谍费尽千辛万苦去偷导弹的源程序，但是只找到了最后一页，结果全都是括号。也有人开玩笑说 Lisp 的缩写其实是 "[**L**ots of **I**rritating **S**illy **P**arentheses](http://www.google.com/search?q=Lots+of+Irritating+Silly+Parentheses)"。

解释器分为两个阶段，第一个阶段是 **parsing**，根据目标语言的语法规则（*syntactic rules*），将程序转换成一个树形结构语法树（*abstract syntax tree*）；第二个阶段是 **execution**，按照语义来执行将前一阶段的结果，从而得到目标。

比如说这是一个计算圆面积的 Lisp 程序：

```scheme
(define r 10)
(* pi (* r r))
```

依次经过上述两阶段之后：

```python
>> program = "(begin (define r 10) (* pi (* r r)))"

>>> parse(program)
['begin', ['define', 'r', 10], ['*', 'pi', ['*', 'r', 'r']]]

>>> eval(parse(program))
314.1592653589793
```

在 Scheme 中，`begin` 的作用是运行其后的所有 `expression` ，并把最后一个 `expression` 的结果当做最终结果。所以 `program` 定义的程序即为计算圆面积的程序。

Scheme 中的对象与 Python 内置对象的对应如下：

```python
Symbol = str              # A Scheme Symbol is implemented as a Python str
Number = (int, float)     # A Scheme Number is implemented as a Python int or float
Atom   = (Symbol, Number) # A Scheme Atom is a Symbol or Number
List   = list             # A Scheme List is implemented as a Python list
Exp    = (Atom, List)     # A Scheme expression is an Atom or List
```

# 第一阶段：Parsing

这一步的处理异常简洁，利用了 Python 内置的 `split()` 函数。

首先是得到源程序的 *tokens* （可以视作程序中有意义的最小代码段，比如所一个数字，一个变量名字）

```python
def tokenize(chars: str) -> list:
    "Convert a string of characters into a list of tokens."
    return chars.replace('(', ' ( ').replace(')', ' ) ').split()
```

`split()` 默认的划分字符是字符串中空格、回车、Tab。

这一步的成果：

```python
>>> program = "(begin (define r 10) (* pi (* r r)))"
>>> tokenize(program)
['(', 'begin', '(', 'define', 'r', '10', ')', '(', '*', 'pi', '(', '*', 'r', 'r', ')', ')', ')']
```

然后就是构造语法树 (*abstract syntax tree*)，并且确保输入程序没有语法错误 (*syntactic error*)。`read_from_tokens()` 递归的将上一步结果转换成树（Python 中的 `list`表示），`atom()` 将 *token* 转换成数字（即 Python 中的 `int` 或 `float`），如果不是数字，那一定是 `symbol` （即 Symbol 对象对应的字符串 `str`)。

```python
def parse(program: str) -> Exp:
    "Read a Scheme expression from a string."
    return read_from_tokens(tokenize(program))

def read_from_tokens(tokens: list) -> Exp:
    "Read an expression from a sequence of tokens."
    if len(tokens) == 0:
        raise SyntaxError('unexpected EOF')
    token = tokens.pop(0)
    if token == '(':
        L = []
        while tokens[0] != ')':
            L.append(read_from_tokens(tokens))
        tokens.pop(0) # pop off ')'
        return L
    elif token == ')':
        raise SyntaxError('unexpected )')
    else:
        return atom(token)

def atom(token: str) -> Atom:
    "Numbers become numbers; every other token is a symbol."
    try: return int(token)
    except ValueError:
        try: return float(token)
        except ValueError:
            return Symbol(token)
```

这一步完成后我们就完成了一半！现在我们能把原程序转换成一个树形结构：

```python
>>> program = "(begin (define r 10) (* pi (* r r)))"

>>> parse(program)
['begin', ['define', 'r', 10], ['*', 'pi', ['*', 'r', 'r']]]
```

马上就能进入第二阶段啦，不过我们得先解释一下运行环境的事。

## 运行环境

运行环境（*environment*）就是程序执行时一个萝卜一个坑的对应。比如说你定义了 x 是数字 10，过一会儿你用到 x 的时候，负责运行你指令的机器怎么知道 x 究竟是 10 还是一条狗呢？负责把变量（*variable*）和他们的值（*value*）对应起来的东西，放在运行环境。这里面不仅放着变量的对应，还放着函数的对应方式。

在这里我们用 Python 中内置的 `dict` 进行这种对应；如果你对 `dict` 不了解的话，可以把他想象成 `map` ；如果你对 `map` 也不了解的话，就把他想象成一个小本本，上面写满了你喜欢的小哥哥和小姐姐，比如说`小姐姐一号`对应`新垣结衣`，`小姐姐二号`对应`Hachi八哥哥`，`小哥哥一号`对应`陈奕迅`等等。

```python
import math
import operator as op

def standard_env():
    "An environment with some Scheme standard procedures."
    env = {}
    env.update(vars(math)) # sin, cos, sqrt, pi, ...
    env.update({
        '+':op.add, '-':op.sub, '*':op.mul, '/':op.truediv, 
        '>':op.gt, '<':op.lt, '>=':op.ge, '<=':op.le, '=':op.eq, 
        'abs':     abs,
        'append':  op.add,  
        'apply':   lambda proc, args: proc(*args),
        'begin':   lambda *x: x[-1],
        'car':     lambda x: x[0],
        'cdr':     lambda x: x[1:], 
        'cons':    lambda x,y: [x] + y,
        'eq?':     op.is_, 
        'equal?':  op.eq, 
        'length':  len, 
        'list':    lambda *x: list(x), 
        'list?':   lambda x: isinstance(x,list), 
        'map':     lambda *args: list(map(*args)),
        'max':     max,
        'min':     min,
        'not':     op.not_,
        'null?':   lambda x: x == [], 
        'number?': lambda x: isinstance(x, Number),   
        'procedure?': callable,
        'round':   round,
        'symbol?': lambda x: isinstance(x, Symbol),
    })
    return env

global_env = standard_env()
```

对 Python 不慎熟悉的同学可能有点蒙圈，这里容我再解释一下。`env` 是一个 `dict`，形式如 `{ r: 10, code_n: 42 }`，`update()` 是 `dict` 添加数据的特有函数，比如 `list` 添加数据的方式是 `append()` 。

```python
env.update(vars(math)) # sin, cos, sqrt, pi, ...
```

这一句中的 `vars(math)`是将 math 模块中所有的函数转换成 `dict` 的形式，然后 `update()` 再将其添加到 `env` 中。

接下来的几行就是 math 中没有的，但 Scheme 默认的运行环境中有的几个函数。其中含有 `lambda`关键词的表达式可以理解为一个函数，冒号前是函数的参数（*parameters*），冒号后是函数的返回值。

比如说：

```python
f = lambda a, b: a + b
```

就声明了一个函数 f ，作用就是取两个参数，返回参数的和，等价于：

```python
def f(a, b):
	return a + b
```

而变量名前带有星号 (*, star, asterisk)，是 Python 中 boxing 与 unboxing 的写法，用来处理参数个数不确定的情况。具体如何使用这里篇幅太小写不下，请检索其他文章吧。

# 第二阶段：Evaluation

在此阶段我们定义了 `eval()` 来运行第一阶段的语法树。不过注意 Python 内置函数也有一个 `eval()`。

写 `eval()` 之前我们来看一下我们都有可能运行什么东西。从 **Syntax** 一栏我们可以看到这里有五种基本情况，前两种分别是 symbol 和 number ，前者可以查找运行环境，后者即是自身。后三种情况有些复杂，是 Lisp 语言中独有的语句。

条件语句 (*condition expression*) ，形如 (`if` *test* *conseq* *alt*)，首先检查 *test* 是真还是假，如果是真，本语句的结果即为 *conseq* 的结果（注意 *conseq* 也可能是一条语句）；如果 *test* 是假，那么本句结果即为 *alt* 的结果（*alt*同样可能是一条语句）。

定义语句 (*definition expression*) 和程式语句 (*procedure call*) 较为简单，就不多解释了。

| Expression                                                   | Syntax                      | Semantics and Example                                        |
| ------------------------------------------------------------ | --------------------------- | ------------------------------------------------------------ |
| [variable reference](http://www.schemers.org/Documents/Standards/R5RS/HTML/r5rs-Z-H-7.html#%_sec_4.1.1) | *symbol*                    | A symbol is interpreted as a variable name; its value is the variable's value.  Example: `r` ⇒ `10` (assuming `r` was previously defined to be 10) |
| [constant literal](http://www.schemers.org/Documents/Standards/R5RS/HTML/r5rs-Z-H-7.html#%_sec_4.1.2) | *number*                    | A number evaluates to itself.  Examples: `12 ⇒ 12` *or* `-3.45e+6 ⇒ -3.45e+6` |
| [conditional](http://www.schemers.org/Documents/Standards/R5RS/HTML/r5rs-Z-H-7.html#%_sec_4.1.5) | `(if` *test conseq alt*`)`  | Evaluate *test*; if true, evaluate and return *conseq*; otherwise *alt*.  Example: `(if (> 10 20) (+ 1 1) (+ 3 3)) ⇒ 6` |
| [definition](http://www.schemers.org/Documents/Standards/R5RS/HTML/r5rs-Z-H-8.html#%_sec_5.2) | `(define` *symbol* *exp*`)` | Define a new variable and give it the value of evaluating the expression *exp*.  Examples: `(define r 10)` |
| [procedure call](http://www.schemers.org/Documents/Standards/R5RS/HTML/r5rs-Z-H-7.html#%_sec_4.1.3) | `(`*proc arg...*`)`         | If *proc* is anything other than the symbols `if` or `define` then it is treated as a procedure. Evaluate *proc* and all the *args*, and then the procedure is applied to the list of *arg* values.  Example: `(sqrt (* 2 8)) ⇒ 4.0` |

所以我们只需要对于语句分类，并且模拟其运行既可以了。

```python
def eval(x: Exp, env=global_env) -> Exp:
    "Evaluate an expression in an environment."
    if isinstance(x, Symbol):        # variable reference
        return env[x]
    elif isinstance(x, Number):      # constant number
        return x                
    elif x[0] == 'if':               # conditional
        (_, test, conseq, alt) = x
        exp = (conseq if eval(test, env) else alt)
        return eval(exp, env)
    elif x[0] == 'define':           # definition
        (_, symbol, exp) = x
        env[symbol] = eval(exp, env)
    else:                            # procedure call
        proc = eval(x[0], env)
        args = [eval(arg, env) for arg in x[1:]]
        return proc(*args)
```

**我们写完啦！**没错，就这么简单。

现在再运行程序，我们就能得到结果啦：

```python
>>> eval(parse("(begin (define r 10) (* pi (* r r)))"))
314.1592653589793
```

是不是很激动！我写出来的时候反正是很激动。

当然，每次用解释器都要调用 `eval(parse("(define something here "))` 似乎有些费力，原作者也写了一个 RPEL 来进行 Read, Parse, Evaluate, Loop 的循环，以及增加了 Nested Environment ，用来实现 Scheme 的`lambda` 。这两个东西我都进行了改写，在下一节一起介绍。

# 加点东西

Norvig 原文中的 `rpel()`有如下的缺点：

- 所有的语句要压缩到一行中

  - 虽然 Lisp 不像 Python 需要用间距进行层次，但是用括号区分层次的做法对可读性太不友好了。
- 输入错误程序就会崩溃，需要从再从 Python 加载。
- 无法退出

所以我写了下面的 `rpel()`：
```python
def repl():
    """read eval print loop, repl"""
    while True:
        try:
            code = read()
           	# input exit to exit 
            if code.strip() == 'exit':
                print("Till next time~")
                break
            val = eval(parse(code))
            # some programs have no output
            if val is not None:
                print(schemestr(val))
        except SyntaxError as e:
            print("[syntax] Something wrong with the syntax of the code:")
            print(e)
            repl()
        except ValueError as e:
            print("[number] Something wrong with the number of the code:")
            print(e)
            repl()
        except:
            print("[unknown] Error unknown, please check")
            repl()


def read():
    code = input("LISP > ")
    while not valid_code(code):
        code += input()
    return code


def valid_code(code):
    count = 0
    for c in code:
        if c == '(':
            count += 1
        elif c == ')':
            if count <= 0:
                raise SyntaxError("Invalid Input")
            count -= 1
    # '('s and ')'s match each other perfectly if count is 0
    return count == 0


def schemestr(exp):
    "Scheme readable form"
    if isinstance(exp, List):
        # list in Python is surrounded by square brackets e.g. [1, 3, 5]
        # rather than parentheses e.g. (1, 3, 5)
        return '(' + ' '.join(map(schemestr, exp)) + ')'
    else:
        return str(exp)

```

其实就一个加强版的 `eval(parse(program))` :-D 弥补了原版的三点缺陷。

其中的 `valide_code` 起到了检查输入是否结束的功能：如果左右括号正好对上，就能说明一个程序输入的结束。`schemestr` 就是把 Python 原生的 list 输出时的左右圆括号改为左右方括号。

## lambda, if, let, cond

上一节结束时的程序无法设计一个带未知参数的函数（如带参数的 lambda 表达式)，因为我们的 `eval()`在运行的时候需要知道在被运行的程序中所有的东西。如果程序有变量，那么 `eval()` 一定要运行环境中知道这变量是什么值。但我们定义一个函数的时候并不知道输入是什么。比如我们想定义一个把输入的数字加一的程序，我们并不一定知道这个输入的数是 0 还是 100。  

这时候就要再次请出我们的运行环境啦。

只有在我们运行的时候才知道那个输入的数字是多少，那我们在运行的时候再将其装入我们的环境就好啦，反正 `lambda` 表达式也只是用于定义程序，而不是用于执行程序。

不过还有一个问题，如果我们在把 `lambda` 表达式中定义的参数名，和在别处定义的变量名，有一样的名字怎么办呢？如果我主程序中有一个变量名叫做 `r`， `lambda` 表达式中也有一个参数叫 `r` ，那之后运行这个表达式定义的函数时，会重新填入 `r` 的值，岂不是把主程序的 `r` 也改写了？

这怎么行呢，那我小本本上的小哥哥小姐姐岂不是都要乱套了？

客官不要着急，这时候只需要再重新找一个小本本，用来记录 `lambda`的小哥哥小姐姐就行了嘛。当然，原来本本上的内容也不能少（除非是被改写了的东西），而 Python 中有个 `ChainMap` 正好是做这个的。

原版是这样写的：

```python
from collections import ChainMap as Environment

class Procedure(object):
    "A user-defined Scheme procedure."
    def __init__(self, parms, body, env):
        self.parms, self.body, self.env = parms, body, env
    def __call__(self, *args):
        env =  Environment(dict(zip(self.parms, args)), self.env)
        return eval(self.body, env)
```

而我进行的改写，细分了两个类：

```python
from collections import ChainMap as Environment

class Procedure(object):
    def __init__(self, parms, body, env):
        self.parms, self.body, self.env = parms, body, env

class ProcedureLambda(Procedure):
    def __call__(self, *args):
        env = Environment(dict(zip(self.parms, args)), self.env)
        return eval(self.body, env)
        
class ProcedureLet(Procedure):
    def result(self):
        self.parms = {parm: eval(arg, self.env) for (parm, arg) in self.parms}
        env = Environment(dict(self.parms), self.env)
        return eval(self.body, env)
```

`ProcedureLambda` 继承了 `Procedure`，和原版的`Procedure`有着一样功能。 而`ProcedureLet` 我一会再解释。

让我们先看一样加强版的 `eval()`。

```python
def eval(x, env=global_env):
    if isinstance(x, Symbol):
        return env[x]
    elif isinstance(x, Number):
        return x
    elif x[0] == 'if':
        (_, test, conseq, alt) = x
        exp = (conseq if eval(test, env) else alt)
        return eval(exp, env)
    elif x[0] == 'cond':
        (_, *body) = x
        exp = ' '
        for (p, e) in body:
            if p == 'else' or eval(p, env):
                exp = e
                break
        return eval(exp, env)
    elif x[0] == 'define':
        (_, symbol, exp) = x
        env[symbol] = eval(exp, env)
    elif x[0] == 'quote':
        (_, exp) = x
        return exp
    elif x[0] == 'lambda':
        (_, parms, body) = x
        return ProcedureLambda(parms, body, env)
    elif x[0] == 'let':
        (_, parms, body) = x
        return ProcedureLet(parms, body, env).result()
    else:  # (proc arg...)
        proc = eval(x[0], env)
        args = [eval(evl, env) for evl in x[1:]]
        return proc(*args)
```

Scheme 中 `lambda` 语句是这样的定义的：

(`lambda` *parms* *body*)，e.g. `(lambda (r) (* pi (* r r)))` *parms* 为参数，*body* 是运行时主体，也是运行时的返回值。

而 `let` 语句是 `lambda` 的语法糖，方便为 `lambda` 的参数设值。而 `let` 语句在运行的时候就可以出结果，所以其 `Procedure` 对象与 `lambda` 的又有所不同，所以 `ProcedureLet` 同样继承了 `Procedure` ，又略有不同。

比如上面的例子如果运行时将 `r` 设为 10，可以用 `let`语句写成下面的程序：

```scheme
(let ((r 10))
	(* pi (* r r)))
```

`cond` 语句是 `if` 的语法糖，如果有多个判断条件时不需要写一堆 `else if` ：

```scheme
(define absolute 
  (lambda (x) 
    (cond ((> x 0) x)
          ((< x 0) (- 0 x))
          (else 0))))
```

这个 cond 语句等价于绝对值函数。

好吧，其实我补充的这两个在源码中很扎眼，一个用了七行代码，一个用法很奇怪，不过我毕竟还没有作者 Peter Norvig 的水平。~~（又不是不能用，这样安慰自己）~~

本来试图用 Scheme 本身的语句来定义 `cond` 与 `let` ，不过原版的 Scheme 还是太简陋啦，实现不了。好在用 Python 进行降维攻击还是可以的。

# 后记

其实在写这个编译器的时候自己已经几乎忘光了 Lisp 的具体语法，几乎每个 keyword 都要查一下具体是怎么做事情的。而且之前也不知道原文中 Python 中 asterisk 的用法，真是从大师那里学到了很多知识。

Lisp 设计的十分的优美。而原文中递归的美令我叹为观止。当然原版 Lisp 还有很多优化和功能，有兴趣的同学可以读一读 [SICP](https://mitpress.mit.edu/sites/default/files/sicp/index.html)。经过拓展后的 Lispy 放在了[GitHub](https://github.com/asuith/mProject/tree/master/lispy) 上，可进行辅助研究，同时如果你也想写一个 Lisp 解释器的话，我还写了一个相应的 test ，可以看看你的完成度有多少。
