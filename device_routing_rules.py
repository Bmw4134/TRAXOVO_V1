
            # Mobile Routing Rules
            @app.route('/mobile-preview')
            def mobile_preview():
                return render_mobile_optimized_view()
            
            @app.route('/desktop-preview') 
            def desktop_preview():
                return render_desktop_full_view()
            
            def detect_device_type(request):
                user_agent = request.headers.get('User-Agent', '').lower()
                if any(mobile in user_agent for mobile in ['iphone', 'android', 'mobile']):
                    return 'mobile'
                return 'desktop'
            