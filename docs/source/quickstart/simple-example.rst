=====================
Simple client example
=====================

.. code-block:: python

    # app.py

    from nineapi.client import Client, APIException

    client = Client()

    try:
        client.log_in('zomgtehlazzers', 'secretnope')
    except APIException as e:
        print('Failed to log in:', e)
    else:
        for post in client.get_posts():
            print(post)
