import bs4

BAD_ATTRS = 'align alink background bgcolor border clear height hspace language link nowrap start text type valign vlink vspace width'.split()

#===============================================================================
class HTMLFormatter(object):
    
    NON_CLOSING = ('hr', 'br', 'link', 'meta', 'img', 'base', 'input', 'param', 'source')
    NO_INDENT = ('body', 'head', 'tbody', 'thead', 'tfoot')
    
    #---------------------------------------------------------------------------
    @classmethod
    def get_tag(cls, el):
        raise NotImplementedError
    
    #---------------------------------------------------------------------------
    @classmethod
    def get_children(cls, el):
        raise NotImplementedError

    #---------------------------------------------------------------------------
    @classmethod
    def get_attrs(cls, el):
        raise NotImplementedError

    #---------------------------------------------------------------------------
    @classmethod
    def get_text(cls, el):
        raise NotImplementedError
    
    #---------------------------------------------------------------------------
    @classmethod
    def get_tail(cls, el):
        raise NotImplementedError
    
    #---------------------------------------------------------------------------
    @classmethod
    def format_element(cls, el, depth=0, prefix='    '):
        indent = prefix * depth
        tag = cls.get_tag(el)
        s = u'{}<{}'.format(indent, tag)
        
        attrs = cls.get_attrs(el)
        for k, v in attrs.items():
            s += u' {}="{}"'.format(k, v)
        
        s += u'>'
        if tag in cls.NON_CLOSING:
            return s + '\n'

        children = cls.get_children(el)
        text = cls.get_text(el)
        if children:
            s += '\n'
            if text:
                s += u'{}{}\n'.format(indent + prefix, text)
            
            for child in children:
                child_tag = cls.get_tag(child)
                if child_tag:
                    s += cls.format_element(
                        child,
                        depth if child_tag in cls.NO_INDENT else depth + 1,
                        prefix
                    )
                else:
                    s += u'{}{}\n'.format(indent + prefix, child.rstrip())
            
            return s + u'{}</{}>\n'.format(indent, tag)

        tail = el.tail.rstrip() if el.tail else ''
        return s + u'{}</{}>{}\n'.format(text, tag, tail)

    #---------------------------------------------------------------------------
    @classmethod
    def format(cls, el, depth=0, prefix='    ', doctype=True):
        raise NotImplementedError


#===============================================================================
class LxmlFormatter(HTMLFormatter):
    
    #---------------------------------------------------------------------------
    @classmethod
    def get_tag(cls, el):
        return el.tag
    
    #---------------------------------------------------------------------------
    @classmethod
    def get_children(cls, el):
        return list(el)

    #---------------------------------------------------------------------------
    @classmethod
    def get_attrs(cls, el):
        return el.attrib or {}
    
    #---------------------------------------------------------------------------
    @classmethod
    def get_text(cls, el):
        return el.text.strip() if el.text else ''

    #---------------------------------------------------------------------------
    @classmethod
    def get_tail(cls, el):
        return el.tail.strip() if el.tail else ''

    #---------------------------------------------------------------------------
    @classmethod
    def format(cls, el, depth=0, prefix='    ', doctype=True):
        st = ''
        if doctype:
            st = el.getroottree().docinfo.doctype if doctype == True else doctype
            st += '\n'
        return st + cls.format_element(el, depth, prefix)


#===============================================================================
class BS4Formatter(HTMLFormatter):
    
    #---------------------------------------------------------------------------
    @classmethod
    def get_tag(cls, el):
        return el.name

    #---------------------------------------------------------------------------
    @classmethod
    def get_attrs(cls, el):
        attrs = {}
        orig = getattr(el, 'attrs', {}) or {}
        for key, values in orig.items():
            attrs[key] = ' '.join(values) if isinstance(values, (list, tuple)) else values
        return attrs
    
    #---------------------------------------------------------------------------
    @classmethod
    def format_element(cls, el, lines, depth=0, prefix='    '):
        indent = prefix * depth
        if isinstance(el, bs4.NavigableString):
            el = el.strip()
            if el:
                lines.append(u'{}{}'.format(indent, el))
            return lines
            
        tag = cls.get_tag(el)
        s = u'{}<{}'.format(indent, tag)
        
        attrs = cls.get_attrs(el)
        for k, v in attrs.items():
            s += u' {}="{}"'.format(k, v)
        
        s += u'>'
        if tag in cls.NON_CLOSING:
            lines.append(s)
            return lines

        children = el.contents
        n_children = len(children)
        if children:
            if n_children > 1 or isinstance(children[0], bs4.Tag):
                lines.append(s)
                for child in children:
                    child_tag = cls.get_tag(child)
                    lines = cls.format_element(
                        child,
                        lines,
                        depth if child_tag in cls.NO_INDENT else depth + 1,
                        prefix
                    )
                lines.append(u'{}</{}>'.format(indent, tag))
                return lines
            else:
                lines.append(u'{}{}</{}>'.format(s, children[0].strip(), tag))
        else:
            lines.append(u'{}</{}>'.format(s, tag))
        return lines

    #---------------------------------------------------------------------------
    @classmethod
    def format(cls, el, depth=0, prefix='    ', doctype=True):
        lines = []
        start = 0
        if isinstance(el, bs4.BeautifulSoup) and el.contents:
            first = el.contents[0]
            if isinstance(first, bs4.Doctype):
                lines.append(unicode(first.output_ready()))
                start = 1

        for child in el.contents[start:]:
            lines = cls.format_element(child, lines, depth, prefix)

        from pprint import pprint
        pprint(lines)
        return u'\n'.join(lines)

#-------------------------------------------------------------------------------
def bs4format(*args, **kws):
    return BS4Formatter.format(*args, **kws)
