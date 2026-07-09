import enum


class UserRole(str, enum.Enum):
    OWNER = "owner"
    MARKETER = "marketer"
    CONTENT_MANAGER = "content_manager"


class AdPlatform(str, enum.Enum):
    META = "meta"
    YOUTUBE = "youtube"
    GOOGLE_ADS = "google_ads"


class AdAccountStatus(str, enum.Enum):
    PENDING = "pending"
    CONNECTED = "connected"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class CampaignObjective(str, enum.Enum):
    AWARENESS = "awareness"
    LAUNCH = "launch"
    SALES = "sales"
    RETARGETING = "retargeting"
    INFLUENCER_COLLAB = "influencer_collab"


class ContentFormat(str, enum.Enum):
    REELS = "reels"
    YOUTUBE_SHORTS = "youtube_shorts"
    YOUTUBE_LONG_FORM = "youtube_long_form"
    STATIC_POST = "static_post"


class CampaignBriefStatus(str, enum.Enum):
    DRAFT = "draft"
    MATCHING = "matching"
    MATCHED = "matched"
    LAUNCHED = "launched"
    COMPLETED = "completed"


class MatchStatus(str, enum.Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ADJUSTED = "adjusted"


class ContentDraftType(str, enum.Enum):
    BLOG = "blog"
    AD_COPY = "ad_copy"
    CREATOR_BRIEF = "creator_brief"
    IMAGE = "image"


class ContentDraftStatus(str, enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"


class InfluencerCategory(str, enum.Enum):
    BEAUTY = "beauty"
    FASHION = "fashion"
    WELLNESS = "wellness"
    FOOD = "food"
    TECH = "tech"
    HOME = "home"
    FITNESS = "fitness"
    PARENTING = "parenting"
    FINANCE = "finance"
    TRAVEL = "travel"
