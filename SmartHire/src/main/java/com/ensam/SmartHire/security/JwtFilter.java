package com.ensam.SmartHire.security;


import com.ensam.SmartHire.service.JwtService;
import com.ensam.SmartHire.service.MyUserDetailsService;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.context.ApplicationContext;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
@Component
public class JwtFilter extends OncePerRequestFilter {
    @Autowired
    private JwtService jwtService;

    @Autowired
    ApplicationContext applicationContext;

    //sending a get/post request with the token so he can get the response
    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain) throws ServletException, IOException {
        String authHeader = request.getHeader("Authorization");
        String token = null;
        String username = null;
        if(request.getCookies()!=null){
            for(Cookie cookie:request.getCookies()){
                if("jwt".equals(cookie.getName())){
                     token = cookie.getValue();
                }
            }
        }
        if(token != null){
            username=jwtService.extractUsername(token);
        }
//        if(authHeader != null && authHeader.startsWith("Bearer ")){
//            token = authHeader.substring(7); // start after Bearer space
//            username = jwtService.extractUsername(token);
//
//        }
        if(username !=null && SecurityContextHolder.getContext().getAuthentication() ==null){

            UserDetails userDetails = applicationContext.getBean(MyUserDetailsService.class).loadUserByUsername(username);
            //validate token then check if user is part of the db
            if(jwtService.validatetoken(token,userDetails)){
                //pass to next filter(UsernamePasswordAuthenticationToken)
                UsernamePasswordAuthenticationToken authToken =
                        new UsernamePasswordAuthenticationToken(userDetails,null,userDetails.getAuthorities());
                authToken.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
                SecurityContextHolder.getContext().setAuthentication(authToken);


            }
        }
        filterChain.doFilter(request,response);
    }

}
