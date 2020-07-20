.. currentmodule:: steam
.. faq:

F.A.Q
======

Find answers to some common questions relating to steam.py and help in the discord server

.. contents:: Questions
    :local:

General
--------

These are some general questions relating to steam.py

How much Python do I need to know?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**A list of useful knowledge courtesy of Scragly:**

    .. I like https://realpython.com for reading up on things as you can see

    - pip installing packages
    - Primitive data types: ``str``, ``int``, ``float``, ``bool``
    - Operators: ``+``, ``-``, ``/``, ``*``, etc.
    - Data structures ``list``, ``tuple``, ``dict``, ``set``
    - Importing
    - Variables, namespace and scope
    - `Control flow <https://realpython.com/python-conditional-statements/>`_
        - ``while``
        - ``if``
        - ``elif``
        - ``else``
        - ``for``
    - `Exception handling <https://realpython.com/python-exceptions/>`_
        - ``try``
        - ``except``
        - ``else``
        - ``finally``
    - `Function definitions <https://realpython.com/defining-your-own-python-function/>`_
    - `Argument definitions <https://realpython.com/python-kwargs-and-args/>`_
        - Argument ordering
        - Default arguments
        - Variable length arguments
    - `Classes, objects, attributes and methods <https://realpython.com/python3-object-oriented-programming/>`_
    - `Console usage, interpreters and environments <https://realpython.com/python-virtual-environments-a-primer/>`_
    - `Asyncio basics <https://realpython.com/async-io-python/>`_
        - ``await``
        - ``async def``
        - ``async with``
        - ``async for``
        - `What is blocking? <https://discordpy.rtfs.io/en/latest/faq.html#what-does-blocking-mean>`_
    - String formatting
        - `str.format() <https://pyformat.info/>`_
        - `f-strings <https://realpython.com/python-f-strings/>`_ A.K.A. formatted string literals
        - Implicit/explicit string concatenation
    - `Logging <https://realpython.com/courses/logging-python/>`_
    - `Decorators <https://realpython.com/primer-on-python-decorators/>`_

You should have knowledge over all of the above this is due to the semi-complex nature of the library along
with asynchronous programming, it can be rather overwhelming for a beginner. Properly learning python will both
prevent confusion and frustration when receiving help from others but will make it easier when reading documentation
and when debugging any issues in your code.

**Places to learn more python**

- https://docs.python.org/3/tutorial/index.html (official tutorial)
- https://greenteapress.com/wp/think-python-2e/ (for beginners to programming or python)
- https://www.codeabbey.com/ (exercises for beginners)
- https://www.real-python.com/ (good for individual quick tutorials)
- https://gto76.github.io/python-cheatsheet/ (cheat sheet)


How can I get help with my code?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**What not to do:**

- Truncate the traceback.
    - As you might remove important parts from it.
- Send screenshots/text files of code/errors unless relevant.
    - As they are difficult to read.
- Use https://pastebin.com,
    - As it is very bloated and ad-heavy.
    - Instead, you could use any of:
        - https://hastebin.com/
        - https://mystb.in/
        - https://gist.github.com/
        - https://starb.in/
- Ask if you can ask a question about the library.
    - The answer will always be yes.
- Saying "This code doesn't work" or "What's wrong with this code?" Without any traceback.
    - This is not helpful for yourself or others. Describe what you expected to happen and/or tried (with your code),
      and what isn't going right. Along with a traceback.

**Encouraged practices:**

- Try searching for something using the documentation or ``=rtfm`` in an appropriate channel.
- Trying something for yourself.

    .. raw:: html

        <video width="480" height="360" controls>
            <source src="https://tryitands.ee/tias.mp4" type="video/mp4">
        Your browser does not support video :(
        </video>


How can I wait for an event?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python3

    @client.event
    async def on_message(message):
        if message.content.startswith("?trade"):

            def check(trade):
                return trade.partner == message.author

            await message.channel.send("Send me a trade!")
            try:
                offer = await bot.wait_for("trade_receive", timeout=60, check=check)
            except asyncio.TimeoutError:
                await message.channel.send("You took too long to send the offer")
            else:
                await message.channel.send(
                    f"You were going to send {len(offer.items_to_receive)} items\n"
                    f"You were going to receive {len(offer.items_to_send)} items"
                )
                await offer.decline()

The final interaction will end up looking something like this:

    User: ?trade

    Bot:  Send me a trade

    User: User sent a new trade offer

    Bot: You were going to send:

    Mann Co. Supply Crate Key, Refined Metal

    You were going to receive:

    Unusual Burning Team Captain


How do I send a trade?
~~~~~~~~~~~~~~~~~~~~~~

Sending a trade should be pretty simple.
You need to first get the inventories of the User's involved.
Then you need to find the items to trade for.
Construct the TradeOffer from its items.
Finally use the `send <https://steampy.rtfd.io/en/latest/api.html#steam.User.send>`_
method on the User that you want to send the offer to.

.. code-block:: python3

    # we need to chose a game to fetch the inventory for
    game = steam.TF2
    # we need to get the inventories to get items
    my_inventory = await client.user.inventory(game)
    their_inventory = await user.inventory(game)

    # we need to get the items to be included in the trade
    keys = my_inventory.filter_items("Mann Co. Supply Crate Key", limit=3)
    earbuds = their_inventory.get_item("Earbuds")

    # finally construct the trade
    trade = TradeOffer(items_to_send=keys, item_to_receive=earbuds, message="This trade was made using steam.py",)
    await user.send(trade=trade)
    # you don't need to confirm the trade manually, the client will handle that for you


What is the difference between fetch and get?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **GET**
    This retrieves an object from the client's cache. If it happened recently, it will be cached.
    So this method is best in this case. This is also the faster of the two methods as it is a dictionary
    lookup.

- **FETCH**
    This retrieves an object from the API, it is also a |coroutine_link|_ because of this.
    This is good in case something needs to be updated, due to the cache being stale or the object not
    being in cache at all. These, however, should be used less frequently as they are a request to the API
    and are generally slower to return values. Fetched values are however added to cache if they aren't
    already in it.
