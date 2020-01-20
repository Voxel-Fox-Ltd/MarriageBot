import bootstrap_builder

# Make page
page = bootstrap_builder.HTMLPage(title="BOT NAME HERE BABEY")

# Build navbar
navcontainer = page.new_navbar(attrs={"class": "navbar-dark bg-dark"})
with navcontainer.new_navbar_nav() as nav:
    nav.new_navbar_nav_item().new_child("a", "BOT NAME HERE BABEY", attrs={"href": "/", "class": "navbar-brand"})
navcontainer.new_child("form", attrs={"class": "form-inline", "action": "/discord_oauth_login", "method": "GET"}).new_child("button", "Login", attrs={"class": "btn btn-outline-success", "type": "submit"})

# Build container
container = page.new_container()
page.shortcuts['container'] = container
page.set_as_default("main")

