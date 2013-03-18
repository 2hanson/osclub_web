# -*- coding: utf-8 -*-
from hashlib import sha1
from datetime import datetime
import logging
import mimetypes
import re
import urllib

from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.markup.templatetags import markup
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.conf import settings
from django.template.defaultfilters import slugify, striptags
from django.utils.translation import ugettext_lazy as _
from django.utils.text import truncate_html_words

from decorators import logtime, once_per_instance


from ckeditor.fields import RichTextField
from djangosphinx.models import SphinxSearch


WORD_LIMIT = getattr(settings, 'ARTICLES_TEASER_LIMIT', 75)
AUTO_TAG = getattr(settings, 'ARTICLES_AUTO_TAG', True)
DEFAULT_DB = getattr(settings, 'ARTICLES_DEFAULT_DB', 'default')
LOOKUP_LINK_TITLE = getattr(settings, 'ARTICLES_LOOKUP_LINK_TITLE', True)

MARKUP_HTML = 'h'
MARKUP_MARKDOWN = 'm'
MARKUP_REST = 'r'
MARKUP_TEXTILE = 't'

#delete by bone
#MARKUP_OPTIONS = getattr(settings, 'ARTICLE_MARKUP_OPTIONS', (
#        (MARKUP_HTML, _('HTML/Plain Text')),
#        (MARKUP_MARKDOWN, _('Markdown')),
#        (MARKUP_REST, _('ReStructured Text')),
#        (MARKUP_TEXTILE, _('Textile'))
#    ))

MARKUP_DEFAULT = getattr(settings, 'ARTICLE_MARKUP_DEFAULT', MARKUP_HTML)

USE_ADDTHIS_BUTTON = getattr(settings, 'USE_ADDTHIS_BUTTON', True)
ADDTHIS_USE_AUTHOR = getattr(settings, 'ADDTHIS_USE_AUTHOR', True)
DEFAULT_ADDTHIS_USER = getattr(settings, 'DEFAULT_ADDTHIS_USER', None)

# regex used to find links in an article
LINK_RE = re.compile('<a.*?href="(.*?)".*?>(.*?)</a>', re.I|re.M)
TITLE_RE = re.compile('<title.*?>(.*?)</title>', re.I|re.M)
TAG_RE = re.compile('[^a-z0-9\-_\+\:\.]?', re.I)

log = logging.getLogger('articles.models')

#其实你好好的思考下 下面的思路其实就是利用了缓存来缓解数据库服务器的压力 如果缓存里面没有的数据 才从数据库里面去取数据
def get_name(user):
    """
    Provides a way to fall back to a user's username if their full name has not
    been entered.
    """

    key = 'username_for_%s' % user.id

    log.debug('Looking for "%s" in cache (%s)' % (key, user))
    name = cache.get(key)
    if not name:
        log.debug('Name not found')

        if len(user.get_full_name().strip()):
            log.debug('Using full name')
            name = user.get_full_name()
        else:
            log.debug('Using username')
            name = user.username

        log.debug('Caching %s as "%s" for a while' % (key, name))
        cache.set(key, name, 86400) #原来django里面自带了cache 我sb了 应该好好利用下的 看了下文档 和gae的使用相同

    return name

#记得吗 直接给对象添加方法就下面这样简单
#>>> class CC():
#...  pass
#... 
#>>> aa=CC()
#>>> def funfun():
#...  print "hi"
#... 
#>>> aa.getName=funfun
#>>> aa.getName()
#hi
User.get_name = get_name

class Tag(models.Model):
    name = models.CharField(max_length=64, unique=True) #这个应该是博客标签的名字
    slug = models.CharField(max_length=64, unique=True, null=True, blank=True) #咋个slug也在里面

    def __unicode__(self):
        return self.name

    @staticmethod
    def clean_tag(name):
        """Replace spaces with dashes, in case someone adds such a tag manually"""

        name = name.replace(' ', '-').encode('utf8', 'ignore')
        #name = TAG_RE.sub('', name)
        clean = name.lower().strip(", ")

        log.debug('Cleaned tag "%s" to "%s"' % (name, clean))
        print('Cleaned tag "%s" to "%s"' % (name, clean))    ######
        return clean

    def save(self, *args, **kwargs):
        """Cleans up any characters I don't want in a URL"""

        log.debug('Ensuring that tag "%s" has a slug' % (self,))
        self.slug = Tag.clean_tag(self.name)
        super(Tag, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return ('articles_display_tag', (self.cleaned,))

    @property
    def cleaned(self):
        """Returns the clean version of the tag"""

        return self.slug or Tag.clean_tag(self.name)

    @property
    def rss_name(self):
        return self.cleaned

    class Meta:
        ordering = ('name',)

class ArticleStatusManager(models.Manager):

    def default(self):
        default = self.all()[:1]

        if len(default) == 0:
            return None
        else:
            return default[0]

class ArticleStatus(models.Model):
    name = models.CharField(max_length=50) #状态里面咋有这个name 是干啥的?
    ordering = models.IntegerField(default=0) #排序 文章排序???
    is_live = models.BooleanField(default=False, blank=True) #文章是否被激活

    objects = ArticleStatusManager()

    class Meta:
        ordering = ('ordering', 'name')
        verbose_name_plural = _('Article statuses')

    def __unicode__(self):
        if self.is_live:
            return u'%s (live)' % self.name
        else:
            return self.name

#分析了下这个文章manager 作用便是对于哪些过期的文章不返回 对于那些激活且有效的文章才返回
class ArticleManager(models.Manager):

    def active(self):
        """
        Retrieves all active articles which have been published and have not
        yet expired.
        """
        now = datetime.now()
        return self.get_query_set().filter(
                Q(expiration_date__isnull=True) |
                Q(expiration_date__gte=now),
                publish_date__lte=now,
                is_active=True)

    def live(self, user=None):
        """Retrieves all live articles"""

        qs = self.active()

        if user is not None and user.is_superuser:
            # superusers get to see all articles
            return qs
        else:
            # only show live articles to regular users
            return qs.filter(status__is_live=True) #这个东西和is_active=True有啥区别????

#MARKUP_HELP = _("""Select the type of markup you are using in this article.
#<ul>
#<li><a href="http://daringfireball.net/projects/markdown/basics" target="_blank">Markdown Guide</a></li>
#<li><a href="http://docutils.sourceforge.net/docs/user/rst/quickref.html" target="_blank">ReStructured Text Guide</a></li>
#<li><a href="http://thresholdstate.com/articles/4312/the-textile-reference-manual" target="_blank">Textile Guide</a></li>
#</ul>""")

#我x 这个article的模型很长很长啊
class Article(models.Model):
    title = models.CharField(max_length=100,verbose_name="标题")
    slug = models.SlugField(unique_for_year='publish_date')  #每年都可以使用相同的slug 注意!
    status = models.ForeignKey(ArticleStatus, default=ArticleStatus.objects.default) #默认值可能是None 或者ArticleStatus的第1个对象
    author = models.ForeignKey(User) #是django自带的user对象
    sites = models.ManyToManyField(Site, blank=True) #from django.contrib.sites.models import Site 是django自带的模型

    keywords = models.TextField(blank=True, help_text=_("If omitted, the keywords will be the same as the article tags.")) #博客的tag真说得上是关键字
    description = models.TextField(blank=True, verbose_name="摘要",help_text=_("If omitted, the description will be determined by the first bit of the article's content.")) #就是摘要了 需要加到文章列表里面 显示一些摘要也行啊 不然仅仅显示标题和作者日期太难看了

    #delete by bone
    #markup = models.CharField(max_length=1, choices=MARKUP_OPTIONS, default=MARKUP_DEFAULT, help_text=MARKUP_HELP) #这个是博客的内容 可以用标记语言写成 需要python 额外模块支持
    content = RichTextField(verbose_name="内容")  #***********models.TextField() changed by bone
    rendered_content = models.TextField() #神马???是标记后的文档???经过markup模块处理后的???

    tags = models.ManyToManyField(Tag, help_text=_('Tags that describe this article'), blank=True) #标签 
    auto_tag = models.BooleanField(default=AUTO_TAG, blank=True, help_text=_('Check this if you want to automatically assign any existing tags to this article based on its content.')) #默认值是true 如何自动tag
    followup_for = models.ManyToManyField('self', symmetrical=False, blank=True, help_text=_('Select any other articles that this article follows up on.'), related_name='followups') #与本文相关的文章 进行followup
    related_articles = models.ManyToManyField('self', blank=True) #晕死 和上面有啥区别???

    publish_date = models.DateTimeField(default=datetime.now, help_text=_('The date and time this article shall appear online.'))
    expiration_date = models.DateTimeField(blank=True, null=True, help_text=_('Leave blank if the article does not expire.')) #可以设置博客过期时间

    is_active = models.BooleanField(default=True, blank=True) #是否激活 发布状态 是草稿 还是final
    login_required = models.BooleanField(blank=True, help_text=_('Enable this if users must login before they can read this article.')) #这个应该不需要吧???哪里体现的???

    use_addthis_button = models.BooleanField(_('Show AddThis button'), blank=True, default=USE_ADDTHIS_BUTTON, help_text=_('Check this to show an AddThis bookmark button when viewing an article.')) #是不是加*的??? 
    addthis_use_author = models.BooleanField(_("Use article author's username"), blank=True, default=ADDTHIS_USE_AUTHOR, help_text=_("Check this if you want to use the article author's username for the AddThis button.  Respected only if the username field is left empty."))
    addthis_username = models.CharField(_('AddThis Username'), max_length=50, blank=True, default=DEFAULT_ADDTHIS_USER, help_text=_('The AddThis username to use for the button.')) #文章分享的功能不知道他是如何实现的???

    #add by bone sphinx search support
    # Or maybe we want to be more.. specific
    search = SphinxSearch(
        index='blog_indexer',
        weights={
            'title': 10, #如果在标题中找到 则权重*10
            'content': 1, #如果在正文找到 则权重*1
            'tags': 5, #如果在标签种找到 则权重*5
            #'author': 100, #如果找的是作者 则权重*100 因为是id 找不到
            'keywords': 10, #如果关键字里面找到 则权重*10
            'description': 10, #如果描述里面找到 则权重*10
        },
        mode='SPH_MATCH_EXTENDED', #扩展查询模式中可以使用如下特殊操作符
        rankmode='SPH_RANK_PROXIMITY_BM25', #目前只在 SPH_MATCH_EXTENDED2 这个匹配模式中提供 这个效果最好
    )
    #增量模式
    #searchdelta = SphinxSearch(
    #    index='index_name delta_name',
    #    weights={
    #        'name': 100,
    #        'description': 10,
    #        'tags': 80,
    #    },
    #    mode='SPH_MATCH_ALL',
    #    rankmode='SPH_RANK_NONE',
    #)
    #add over

    objects = ArticleManager()

    def __init__(self, *args, **kwargs):
        """Makes sure that we have some rendered content to use"""

        super(Article, self).__init__(*args, **kwargs)

        self._next = None
        self._previous = None
        self._teaser = None

        if self.id:
            # mark the article as inactive if it's expired and still active
            if self.expiration_date and self.expiration_date <= datetime.now() and self.is_active:
                self.is_active = False
                self.save() #为啥在初始化的时候就save这个对象到数据库???--这里貌似是已经存了的,立即又存,我也不懂

            if not self.rendered_content or not len(self.rendered_content.strip()):
                self.save()

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        """Renders the article using the appropriate markup language."""

        using = kwargs.get('using', DEFAULT_DB)

        ###self.do_render_markup() #delete by bone
        self.rendered_content = self.content #add by bone
        self.do_addthis_button()
        self.do_meta_description()
        self.do_unique_slug(using)

        super(Article, self).save(*args, **kwargs)

        # do some things that require an ID first
        requires_save = self.do_auto_tag(using)
        requires_save |= self.do_tags_to_keywords()
        requires_save |= self.do_default_site(using)

        if requires_save:
            # bypass the other processing
            super(Article, self).save()
    
    #delete this function
    #def do_render_markup(self):
        """Turns any markup into HTML"""

        #original = self.rendered_content
        #delete by bone
        #if self.markup == MARKUP_MARKDOWN:
        #    self.rendered_content = markup.markdown(self.content)
        #elif self.markup == MARKUP_REST:
        #    self.rendered_content = markup.restructuredtext(self.content)
        #elif self.markup == MARKUP_TEXTILE:
        #    self.rendered_content = markup.textile(self.content)
        #else:
        #    self.rendered_content = self.content
        
        
        #self.rendered_content = self.content #to add highlight javascript
        #return (self.rendered_content != original)

    def do_addthis_button(self):
        """Sets the AddThis username for this post"""

        # if the author wishes to have an "AddThis" button on this article,
        # make sure we have a username to go along with it.
        if self.use_addthis_button and self.addthis_use_author and not self.addthis_username:
            self.addthis_username = self.author.username
            return True

        return False

    def do_unique_slug(self, using=DEFAULT_DB):
        """
        Ensures that the slug is always unique for the year this article was
        posted
        """
        # Changed by Spark.
        if not self.id:
            # make sure we have a slug first
            #if not len(self.slug.strip()):
            #    self.slug = slugify(self.title)
            self.slug = "-".join(self.title.strip().split())
            self.slug = self.get_unique_slug(self.slug, using)
            
            return True
        else :
            self.slug = "-".join(self.title.strip().split())
            self.slug = self.get_unique_slug(self.slug, using)       
            return False

    def do_tags_to_keywords(self):
        """
        If meta keywords is empty, sets them using the article tags.

        Returns True if an additional save is required, False otherwise.
        """

        if len(self.keywords.strip()) == 0:
            self.keywords = ', '.join([t.name for t in self.tags.all()])
            return True

        return False

    def do_meta_description(self):
        """
        If meta description is empty, sets it to the article's teaser.

        Returns True if an additional save is required, False otherwise.
        """

        if len(self.description.strip()) == 0:
            self.description = self.teaser
            return True

        return False

    @logtime
    @once_per_instance
    def do_auto_tag(self, using=DEFAULT_DB):
        """
        Performs the auto-tagging work if necessary.

        Returns True if an additional save is required, False otherwise.
        """

        if not self.auto_tag:
            log.debug('Article "%s" (ID: %s) is not marked for auto-tagging. Skipping.' % (self.title, self.pk))
            return False

        # don't clobber any existing tags!
        existing_ids = [t.id for t in self.tags.all()]
        log.debug('Article %s already has these tags: %s' % (self.pk, existing_ids))

        unused = Tag.objects.all()
        if hasattr(unused, 'using'):
            unused = unused.using(using)
        unused = unused.exclude(id__in=existing_ids)

        found = False
        to_search = (self.content, self.title, self.description, self.keywords)
        for tag in unused:
            regex = re.compile(r'\b%s\b' % tag.name, re.I)
            if any(regex.search(text) for text in to_search):
                log.debug('Applying Tag "%s" (%s) to Article %s' % (tag, tag.pk, self.pk))
                self.tags.add(tag)
                found = True

        return found

    def do_default_site(self, using=DEFAULT_DB):
        """
        If no site was selected, selects the site used to create the article
        as the default site.

        Returns True if an additional save is required, False otherwise.
        """

        if not len(self.sites.all()):
            sites = Site.objects.all()
            if hasattr(sites, 'using'):
                sites = sites.using(using)
            self.sites.add(sites.get(pk=settings.SITE_ID))
            return True

        return False

    def get_unique_slug(self, slug, using=DEFAULT_DB):
        """Iterates until a unique slug is found"""

        # we need a publish date before we can do anything meaningful
        if type(self.publish_date) is not datetime:
            return slug

        orig_slug = slug
        year = self.publish_date.year
        counter = 1

        while True:
            not_unique = Article.objects.all()
            if hasattr(not_unique, 'using'):
                not_unique = not_unique.using(using)
            not_unique = not_unique.filter(publish_date__year=year, slug=slug)

            if len(not_unique) == 0:
                return slug

            slug = '%s-%s' % (orig_slug, counter)
            counter += 1
    
    #此函数可以找到一篇文章里面所有的链接 晕死 他还去爬人家的网页 获取网页的title之类的 是不是浪费了点
    def _get_article_links(self):
        """
        Find all links in this article.  When a link is encountered in the
        article text, this will attempt to discover the title of the page it
        links to.  If there is a problem with the target page, or there is no
        title (ie it's an image or other binary file), the text of the link is
        used as the title.  Once a title is determined, it is cached for a week
        before it will be requested again.
        """

        links = []

        # find all links in the article
        log.debug('Locating links in article: %s' % (self,))
        for link in LINK_RE.finditer(self.rendered_content):
            url = link.group(1)
            log.debug('Do we have a title for "%s"?' % (url,))
            key = 'href_title_' + sha1(url).hexdigest()

            # look in the cache for the link target's title
            title = cache.get(key)
            if title is None:
                log.debug('Nope... Getting it and caching it.')
                title = link.group(2)

                if LOOKUP_LINK_TITLE:
                    try:
                        log.debug('Looking up title for URL: %s' % (url,))
                        # open the URL
                        c = urllib.urlopen(url)
                        html = c.read()
                        c.close()

                        # try to determine the title of the target
                        title_m = TITLE_RE.search(html)
                        if title_m:
                            title = title_m.group(1)
                            log.debug('Found title: %s' % (title,))
                    except:
                        # if anything goes wrong (ie IOError), use the link's text
                        log.warn('Failed to retrieve the title for "%s"; using link text "%s"' % (url, title))

                # cache the page title for a week
#                log.debug('Using "%s" as title for "%s"' % (title, url))
                cache.set(key, title, 604800)

            # add it to the list of links and titles
            if url not in (l[0] for l in links):
                links.append((url, title))

        return tuple(links)
    links = property(_get_article_links)

    #对于统计汉字个数无效 需要修改
    def _get_word_count(self):
        """Stupid word counter for an article."""

        import re
        cjkReg = re.compile(u'[\u1100-\uFFFDh]+?')
        inputString = striptags(self.rendered_content)
        trimedCJK = cjkReg.sub( ' a ', inputString, 0)
        return len(trimedCJK.split())
    word_count = property(_get_word_count)

    @models.permalink
    def get_absolute_url(self):
        return ('articles_display_article', (self.publish_date.year, self.slug))

    def _get_teaser(self):
        """
        Retrieve some part of the article or the article's description.
        """
        if not self._teaser:
            if len(self.description.strip()):
                self._teaser = self.description
            else:
                self._teaser = truncate_html_words(self.rendered_content, WORD_LIMIT)

        return self._teaser
    teaser = property(_get_teaser)
    
    #由此看获取上下一篇文章均是根据出版日期来的 并且还是显示第一篇文章和最后一篇文章 是不是bug???
    def get_next_article(self):
        """Determines the next live article"""

        if not self._next:
            try:
                qs = Article.objects.live().exclude(id__exact=self.id)
                article = qs.filter(publish_date__gte=self.publish_date).order_by('publish_date')[0]
            except (Article.DoesNotExist, IndexError):
                article = None
            self._next = article

        return self._next

    def get_previous_article(self):
        """Determines the previous live article"""

        if not self._previous:
            try:
                qs = Article.objects.live().exclude(id__exact=self.id) #排除文章在filter里面 学到!!!
                article = qs.filter(publish_date__lte=self.publish_date).order_by('-publish_date')[0]
            except (Article.DoesNotExist, IndexError):
                article = None
            self._previous = article

        return self._previous

    class Meta:
        ordering = ('-publish_date', 'title')
        get_latest_by = 'publish_date'

class Attachment(models.Model):
    upload_to = lambda inst, fn: 'attach/%s/%s/%s' % (datetime.now().year, inst.article.slug, fn)

    article = models.ForeignKey(Article, related_name='attachments')
    attachment = models.FileField(upload_to=upload_to)
    caption = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ('-article', 'id')

    def __unicode__(self):
        return u'%s: %s' % (self.article, self.caption)

    @property
    def filename(self):
        return self.attachment.name.split('/')[-1]

    @property
    def content_type_class(self):
        mt = mimetypes.guess_type(self.attachment.path)[0]
        if mt:
            content_type = mt.replace('/', '_')
        else:
            # assume everything else is text/plain
            content_type = 'text_plain'

        return content_type

