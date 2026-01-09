package com.example.playtracker.data.remote.service

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import okhttp3.OkHttpClient
import java.util.concurrent.TimeUnit

object RetrofitInstance {
//    private const val BASE_URL = "http://192.168.18.191:8000/"
//    private const val BASE_URL = "https://playtracker.antoniogalvezdel.dev/"
    private const val BASE_URL = "https://playtracker-backend.onrender.com"

    // Cliente con timeouts aumentados
    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .writeTimeout(60, TimeUnit.SECONDS)
        .build()

    private val retrofit: Retrofit by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }

    val api: AuthApi by lazy { retrofit.create(AuthApi::class.java) }
    val gameApi: GameApi by lazy { retrofit.create(GameApi::class.java) }
    val userApi: UserApi by lazy { retrofit.create(UserApi::class.java) }
    val userGameApi: UserGameApi by lazy { retrofit.create(UserGameApi::class.java) }
    val friendsApi: FriendsApi by lazy { retrofit.create(FriendsApi::class.java) }
    val reviewsApi: ReviewsApi by lazy { retrofit.create(ReviewsApi::class.java) }
    val recommendationsApi: RecommendationsApi by lazy { retrofit.create(RecommendationsApi::class.java) }
}