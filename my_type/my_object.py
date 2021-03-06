#!/usr/bin/env python
#-*- coding: utf-8 -*-

#from ufp.terminal.debug import print_ as debug
import uuid
import json
import sys
if sys.version_info < (3, ):
    from ..exception import Exception as MozException

# from .my_function import Function
# from .my_array import Array
# from .my_raw import Raw
# from .my_util import convertToJs


class Object(object):
    """
    javascript object에 대한 인터페이스를 제공합니다.

    + 사전 형식으로 속성에 접근할 수 있습니다(__getitem__, __setitem__, __delitem__).
    + 속성 형식으로 속성에 접근 할 수 있습니다(__getattr__, __setattr__, __delattr__).
    + __eq__, __contains__ 메소드가 구현되어 있습니다.

    만약, 이 객체에 존재하는 속성의 이름과 같은 자바스크립트 오브젝트의 속성에 접근하려면, 사전 형식으로 원소에 접근하십시오.

    사용 예는 다음과 같습니다.

    .. code-block:: python

        >>> import mozrepl
        >>> repl = mozrepl.Mozrepl()
        >>> a = repl.execute('repl')
        >>> b = repl.execute('repl')
        >>> a == b # __eq__
        True
        >>> '_name' in a # __contains__
        True
        >>> a._name # __getattr__
        u'repl'
        >>> a['_name'] # __getitem__
        u'repl'
        >>> a['_name'] = 'pymozrepl' # __setitem__
        >>> a['_name']
        u'pymozrepl'
        >>> del a._name # __delattr__
        >>> a._name
        None
        >>> for key, value in a: # __iter__
        ...
    """

    def __init__(self, repl, uuid):
        self.__dict__['_repl'] = repl
        self.__dict__['_uuid'] = uuid
        # print('\n EMPIEZA >','-',repl,'-',uuid)

    @classmethod
    def makeNotinited(cls, repl):
        """
        초기화되지 않은 참조 오브젝트를 얻습니다.

        :param repl: mozrepl.Mozrepl 객체
        :type repl: :py:class:`~mozrepl.Mozrepl`
        :return: 초기화되지 않은 :py:class:`~mozrepl.type.Object` 객체.
        :rtype: :py:class:`~mozrepl.type.Object`
        """
        buffer = str(uuid.uuid4())
        return cls(repl, buffer)

    def __str__(self):
        """
        자바스크립트에서 이 오브젝트에 대한 참조값.

        만약, 자바스크립트에서 직접 이 오브젝트에 대해 접근하기를 원한다면, 이 속성을 통해 변수 이름을 얻을 수 있습니다. 예컨데, 다음과 같이 사용 할 수 있습니다.

        .. code-block:: python

            >>> import mozrepl
            >>> repl = mozrepl.Mozrepl()
            >>> obj = repl.execute('window')
            >>> unicode(obj)
            u'__pymozrepl_c8d7323280c54d09809e2dd7d34d1c70.ref["1e1c7ae3-c1fc-4664-b57f-1281bdc1c996"]'
            >>> repl.execute('var value = {reference}'.format(reference=obj))
        """
        return '{baseVar}.ref["{uuid}"]'.format(
            baseVar=self._repl._baseVarname, uuid=self._uuid)

    def __eq__(self, other):
        buffer = '{other} == {reference};'.format(
            other=convertToJs(other), reference=self)
        return self._repl.execute(buffer)

    def __contains__(self, item):
        buffer = '{item} in {reference};'.format(
            item=convertToJs(item), reference=self)
        return self._repl.execute(buffer)

    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        self[name] = repr(value)

    def __delattr__(self, name):
        del self[name]

    def __iter__(self):
        """
        iterador para acceder al objeto javascript.

        : Rendimiento: valor; Si usted __iterator__ 'existe la propiedad en el objeto, se utiliza un iterador para realizar la tarea.
        : Rendimiento: A menos iteradores definidos de otro modo, (valor clave, pares) para aprobar.
        print('nidos de otro modo, (valor clave, pares) para aprobar.')
        """
        buffer = """(function(reference){{ var processValue = function(value){{ var type = typeof value; if ( type == 'object' || type == 'function' ) {{ if ( type == 'object' && Array.isArray(value) ) {{ type = 'array'; }}; var uuid = {baseVar}.modules.uuid.uuid(); {baseVar}.ref[uuid] = value; return {{ 'uuid' : uuid.toString(), 'type' : type }}; }}; return {{ 'value' : value }}; }}; let iter; if ( '__iterator__' in reference ) {{ iter = function* (){{ for (let value in Iterator(reference)) {{ let robj = [ processValue(value) ]; yield JSON.stringify(robj); }}; }}; }} else {{ iter = function* (){{ for (let [key, value] in Iterator(reference)) {{ let robj = [ processValue(key), processValue(value) ]; yield JSON.stringify(robj); }}; }}; }}; return {{ 'iter': iter(), 'next': function(){{ let buffer = this.iter.next(); if ( buffer.done ) {{ throw {{ 'name': 'StopIteration' }}; }}; return buffer.value; }} }}; }}({reference}));""".format(
            reference=self, baseVar=self._repl._baseVarname)
        iter = self._repl.execute(buffer)
        while True:
            robj = self._repl.execute('{iter}.next();'.format(iter=iter))
            if not robj:
                raise StopIteration
            items = list()
            robj = json.loads(robj, strict=False)
            for item in robj:
                if 'type' in item:
                    if item['type'] == 'object':
                        items.append(Object(self._repl, item['uuid']))
                    elif item['type'] == 'array':
                        items.append(Array(self._repl, item['uuid']))
                    elif item['type'] == 'function':
                        items.append(Function(self._repl, item['uuid']))
                else:
                    items.append(item.get('value', None))
            if len(items) == 1:
                yield items[0]
            elif len(items) == 2 and type(items[0]) == int:
                yield tuple(items)[1]
            else:
                yield tuple(items)
        pass

    def __repr__(self):
        buffer = """{baseVar}.modules.represent({reference});""".format(
            reference=self, baseVar=self._repl._baseVarname)
        return self._repl.execute(buffer)

    def __getitem__(self, key):
        key = convertToJs(key)
        buffer = '{reference}[{key}]'.format(reference=self, key=key)
        item = self._repl.execute(buffer)
        if isinstance(item, Function):
            buffer = '{reference}[{key}].bind({reference})'.format(
                reference=self, key=key)
            item = self._repl.execute(buffer)
        return item

    def __setitem__(self, key, value):
        buffer = '{reference}[{key}] = {value}; null;'.format(
            reference=self, key=convertToJs(key), value=value)
        self._repl._rawExecute(buffer)

    def __delitem__(self, key):
        buffer = 'delete {reference}[{key}]; null;'.format(
            reference=self, key=convertToJs(key))
        self._repl._rawExecute(buffer)

    def __del__(self):
        buffer = 'delete {reference}; null;'.format(reference=self)
        self._repl._rawExecute(buffer)

    def __dir__(self):
        # buffer = 'Object.keys({reference});'.format(reference=self)
        # dir(self)
        res = [i[1].name for i in self.attributes]
        return res

    def click_wait(self):
        self.click()
        self.waitLoad()


from .my_array import Array
from .my_function import Function
from .my_util import convertToJs
# from .my_raw import Raw