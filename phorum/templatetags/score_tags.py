import warnings
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def cache_thread_children(queryset, max_roots=10):
    """
    django-mptt's cache_tree_children modified in a way that it returns
    replies nested only one level deeper than the root node.

    Returns list of max_roots nodes.
    """
    current_path = []
    top_nodes = []

    # If ``queryset`` is QuerySet-like, set ordering to depth-first
    if hasattr(queryset, 'order_by'):
        mptt_opts = queryset.model._mptt_meta
        tree_id_attr = mptt_opts.tree_id_attr
        left_attr = mptt_opts.left_attr
        if tuple(queryset.query.order_by) != (tree_id_attr, left_attr):
            warnings.warn(
                (
                    "cache_tree_children() was passed a queryset with the wrong ordering: %r.\n"
                    "This will cause an error in mptt 0.8."
                ) % (queryset.query.order_by,),
                UserWarning,
            )
            queryset = queryset.order_by(tree_id_attr, left_attr)

    if queryset:
        # Get the model's parent-attribute name
        parent_attr = queryset[0]._mptt_meta.parent_attr
        root_level = None
        for obj in queryset:
            # Get the current mptt node level
            node_level = obj.get_level()

            if root_level is None:
                # First iteration, so set the root level to the top node level
                root_level = node_level

            # Set up the attribute on the node that will store cached children,
            # which is used by ``MPTTModel.get_children``
            obj._cached_children = []

            # Remove nodes not in the current branch
            while len(current_path) > node_level - root_level:
                current_path.pop(-1)

            if node_level == root_level:
                # Add the root to the list of top nodes, which will be returned
                top_nodes.append(obj)
            else:
                # Cache the parent on the current node, and attach the current
                # node to the root's list of children
                _parent = current_path[0]
                setattr(obj, parent_attr, _parent)
                _parent._cached_children.append(obj)
                setattr(obj, 'real_parent', current_path[-1])

                if root_level == 0:
                    # get_ancestors() can use .parent.parent.parent...
                    setattr(obj, '_mptt_use_cached_ancestors', True)

            # Add the current node to end of the current path - the last node
            # in the current path is the parent for the next iteration, unless
            # the next iteration is higher up the tree (a new branch), in which
            # case the paths below it (e.g., this one) will be removed from the
            # current path during the next iteration
            current_path.append(obj)

    # sort children by creation time
    for node in top_nodes:
        node._cached_children = sorted(node._cached_children, key=lambda x: x.created)

    # return last 'max_roots' of nodes (reversed)
    return sorted(top_nodes, key=lambda x: x.created, reverse=True)[:min(max_roots, len(top_nodes))]


class DiscussionThreadNode(template.Node):
    def __init__(self, template_nodes, queryset_var):
        self.template_nodes = template_nodes
        self.queryset_var = queryset_var

    def _render_node(self, context, node):
        bits = []
        context.push()
        for child in node.get_children():
            bits.append(self._render_node(context, child))
        context['node'] = node
        context['children'] = mark_safe(''.join(bits))
        rendered = self.template_nodes.render(context)
        context.pop()
        return rendered

    def render(self, context):
        queryset = self.queryset_var.resolve(context)
        roots = cache_thread_children(queryset)
        bits = [self._render_node(context, node) for node in roots]
        return ''.join(bits)


@register.tag
def discussionthread(parser, token):
    """
    Tag for rendering of discussion threads - first node has list of children that
    are flattened and ordered by date, no matter how nested they are in the MPTT
    structure. Usage similar to django-mppt's recursetree tag (in fact, it's heavily
    based on it).
    """
    bits = token.contents.split()
    if len(bits) != 2:
        raise template.TemplateSyntaxError('%s tag requires a queryset' % bits[0])

    queryset_var = template.Variable(bits[1])

    template_nodes = parser.parse(('enddiscussionthread',))
    parser.delete_first_token()

    return DiscussionThreadNode(template_nodes, queryset_var)
