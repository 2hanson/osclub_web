# -*- coding: utf-8 -*-
import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage
from django.core.urlresolvers import reverse
from django.http import HttpResponsePermanentRedirect, Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from articles.models import Article, Tag
from datetime import datetime
from re import findall

ARTICLE_PAGINATION = getattr(settings, 'ARTICLE_PAGINATION', 20)

#add by bone
#Brush aliases and his File name(for sytax highlight)
BRUSH_JSFILE={
  "as3":"shBrushAS3.js","actionscript3":"shBrushAS3.js",
  "bash":"shBrushBash.js","shell":"shBrushBash.js",
  "cf":"shBrushColdFusion.js","coldfusion":"shBrushColdFusion.js",
  "c-sharp":"shBrushCSharp.js","csharp":"shBrushCSharp.js",
  "cpp":"shBrushCpp.js","c":"shBrushCpp.js",
  "css":"shBrushCss.js",
  "delphi":"shBrushDelphi.js","pas":"shBrushDelphi.js","pascal":"shBrushDelphi.js",
  "diff":"shBrushDiff.js","patch":"shBrushDiff.js",
  "erl":"shBrushErlang.js","erlang":"shBrushErlang.js",
  "groovy":"shBrushGroovy.js",
  "js":"shBrushJScript.js","jscript":"shBrushJScript.js","javascript":"shBrushJScript.js",
  "java":"shBrushJava.js",
  "jfx":"shBrushJavaFX.js","javafx":"shBrushJavaFX.js",
  "perl":"shBrushPerl.js","pl":"shBrushPerl.js",
  "php":"shBrushPhp.js",
  "plain":"shBrushPlain.js","text":"shBrushPlain.js",
  "ps":"shBrushPowerShell.js","powershell":"shBrushPowerShell.js",
  "py":"shBrushPython.js","python":"shBrushPython.js",
  "rails":"shBrushRuby.js","ror":"shBrushRuby.js","ruby":"shBrushRuby.js",
  "scala":"shBrushScala.js",
  "sql":"shBrushSql.js",
  "vb":"shBrushVb.js","vbnet":"shBrushVb.js",
  "xml":"shBrushXml.js","xhtml":"shBrushXml.js","xslt":"shBrushXml.js","html":"shBrushXml.js","xhtml":"shBrushXml.js",  
}
#sytax highlight style
HIGHLIGHT_STYLE={
  "Default":"shThemeDefault.css",
  "Django":"shThemeDjango.css",
  "Eclipse":"shThemeEclipse.css",
  "Emacs":"shThemeEmacs.css",
  "FadeToGrey":"shThemeFadeToGrey.css",
  "Midnight":"shThemeMidnight.css",
  "RDark":"shThemeRDark.css",
}
#add over

log = logging.getLogger('articles.views')

#除了ajax自动补全 还有rss atom以外 所有的显示博客的视图功能都在这里了 Yes, it's dirty to have so many URLs go to one view
#很简单 就是几个template 加文章数据 一取出来就显示而已
def display_blog_page(request, tag=None, username=None, year=None, month=None, page=1):
    """
    Handles all of the magic behind the pages that list articles in any way.
    Yes, it's dirty to have so many URLs go to one view, but I'd rather do that
    than duplicate a bunch of code.  I'll probably revisit this in the future.
    """
    
    authorMap = {}
    authorArchives = []
    res = Article.objects.all()
    for r in res :
        if authorMap.has_key(r.author.username) == False :
            authorMap[r.author.username] = 1
        else :
            authorMap[r.author.username] = authorMap[r.author.username] + 1
    
    authorMap.keys().sort()
    for k in authorMap.keys() :
        authorArchives.append((k, authorMap[k]))
        
    context = {'request': request, 'authorArchives': authorArchives}
    if tag:
        try:
            tag = get_object_or_404(Tag, slug__iexact=tag) #from articles.models import Article, Tag 看来是在Tag的模型里面去找
        except Http404:
            # for backwards-compatibility
            tag = get_object_or_404(Tag, name__iexact=tag) #咋个前面是去获取slug 这里又是去获取name呢???

        articles = tag.article_set.live(user=request.user).select_related() #ArticleManager里面有live这个方法 但是article里面没有这个方法啊 objects = ArticleManager()???奇怪
        template = 'articles/display_tag.html'
        context['tag'] = tag

    elif username:
        # listing articles by a particular author
        user = get_object_or_404(User, username=username)
        articles = user.article_set.live(user=request.user)
        template = 'articles/by_author.html'
        context['author'] = user

    elif year and month:
        # listing articles in a given month and year
        year = int(year)
        month = int(month)
        articles = Article.objects.live(user=request.user).select_related().filter(publish_date__year=year, publish_date__month=month) #select_related()可以缓存查询
        template = 'articles/in_month.html'
        context['month'] = datetime(year, month, 1)

    else:
        # listing articles with no particular filtering
        articles = Article.objects.live(user=request.user)
        template = 'articles/article_list.html'

    # paginate the articles
    paginator = Paginator(articles, ARTICLE_PAGINATION,
                          orphans=int(ARTICLE_PAGINATION / 4))
    try:
        page = paginator.page(page)
    except EmptyPage:
        raise Http404

    context.update({'paginator': paginator,
                    'page_obj': page})
    variables = RequestContext(request, context)
    response = render_to_response(template, variables)

    return response

def search_article(request,page=1):
    if request.method == 'POST':
        query=request.POST.get('query',None)
        if query==None:
            template = 'articles/article_list.html'
        else:    
            #return HttpResponse("you search "+query)  
            r=Article.search.query(query)     
            #listing articles with no particular filtering
            articles = list(r)
            context={'articles':articles,'query':query,'search_meta':r._sphinx}
            template = 'articles/article_search.html'
               
        # paginate the articles
        paginator = Paginator(articles, ARTICLE_PAGINATION,
                              orphans=int(ARTICLE_PAGINATION / 4))
        try:
            page = paginator.page(page)
        except EmptyPage:
            raise Http404

        context.update({'paginator': paginator,
                        'page_obj': page})
        variables = RequestContext(request, context)
        response = render_to_response(template, variables)

        return response
    else:
        #return HttpResponse("fuck off")
        raise Http404  
    
def display_article(request, year, slug, template='articles/article_detail.html'):
    """Displays a single article."""

    try:
        article = Article.objects.live(user=request.user).get(publish_date__year=year, slug=slug)
    except Article.DoesNotExist:
        raise Http404

    # make sure the user is logged in if the article requires it
    if article.login_required and not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('auth_login') + '?next=' + request.path)

    #add by bone if this article needs to code highlight then use syntaxhighlighter
    #<pre class="brush:python;">
    #<pre class="brush:python;collapse:true;ruler:true;wrap-lines:false;">
    #maybe should be stronger
    brushes=findall(r'<pre class="brush:(\w+);',article.rendered_content)     
    jsfile2load=list(set([BRUSH_JSFILE[brush] for brush in brushes]))   #avoid to multi load js files    
    #style=findall(r'theme:(\w+)',article.rendered_content) 
    style=findall(r'<!--\s*code_highlight_theme:\s*(\w+)\s*-->',article.rendered_content)
    highlight_style=HIGHLIGHT_STYLE['Default'] #default highlight style
    last_style_index=len(style)-1
    if last_style_index>=0 and style[last_style_index].capitalize() in HIGHLIGHT_STYLE.keys():
        highlight_style=HIGHLIGHT_STYLE[style[last_style_index].capitalize()] #choose only one style
    print "highlight_style:",highlight_style    
    #add over
    
    variables = RequestContext(request, {
        'article': article,
        'disqus_forum': getattr(settings, 'DISQUS_FORUM_SHORTNAME', None),
        'jsfile2load':jsfile2load, #load SyntaxHighlighter js file
        'highlight_style':highlight_style,
    })
    response = render_to_response(template, variables)

    return response

def redirect_to_article(request, year, month, day, slug):
    # this is a little snippet to handle URLs that are formatted the old way.
    article = get_object_or_404(Article, publish_date__year=year, slug=slug)
    return HttpResponsePermanentRedirect(article.get_absolute_url())

def ajax_tag_autocomplete(request):
    """Offers a list of existing tags that match the specified query"""

    if 'q' in request.GET:
        q = request.GET['q']
        key = 'ajax_tag_auto_%s' % q
        response = cache.get(key)

        if response is not None:
            return response

        tags = list(Tag.objects.filter(name__istartswith=q)[:10])
        response = HttpResponse(u'\n'.join(tag.name for tag in tags))
        cache.set(key, response, 300)

        return response

    return HttpResponse()

